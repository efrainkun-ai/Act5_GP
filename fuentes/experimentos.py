"""Entrenamiento reproducible, evaluación reservada y registro real en MLflow."""

import hashlib
import json
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import scipy
import sklearn
from mlflow.tracking import MlflowClient
from scipy.stats import binomtest
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, roc_curve, classification_report, confusion_matrix
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import label_binarize
from sklearn.svm import LinearSVC

from datos_prep import preparar_datos
from obtener_datos import obtener_datos, huella


def guardar(obj, path):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def metricas(y, pred):
    return {"accuracy": accuracy_score(y,pred),
            "precision_macro": precision_score(y,pred,average="macro",zero_division=0),
            "recall_macro": recall_score(y,pred,average="macro",zero_division=0),
            "f1_macro": f1_score(y,pred,average="macro",zero_division=0)}


def ejecutar_experimentos(raiz, tracking_dir):
    raiz, tracking_dir = Path(raiz).resolve(), Path(tracking_dir).resolve()
    ev = raiz / "evidencias" / "entrenamiento_v1"
    figs = ev / "figuras"
    models = tracking_dir / "modelos_exportados"
    for p in [ev,figs,models]: p.mkdir(parents=True,exist_ok=True)
    seed = 42
    inicio = int(time.time()*1000)
    lock = json.loads((raiz/"datos/dataset.lock.json").read_text())
    obtener_datos(raiz/"datos/datos_ini", raiz/"evidencias/dataset_obtencion.json", solo_verificar=False)
    raw, clean, quality = preparar_datos(raiz/"datos/datos_ini"/lock["archivo_csv"],raiz/"datos/datos_limp",ev)
    train,test=train_test_split(clean,test_size=.2,stratify=clean.intent_clean,random_state=seed)
    assert set(train.text_sha256).isdisjoint(set(test.text_sha256))
    split = pd.concat([train.assign(split="train"),test.assign(split="test")])[["source_row","text_sha256","split"]]
    split.to_csv(raiz/"datos/datos_limp/split_v1.csv",index=False)
    fold_ids=np.full(len(train),-1,dtype=int)
    folds=list(StratifiedKFold(n_splits=5,shuffle=True,random_state=seed).split(train.text_clean,train.intent_clean))
    for k,(_,validation) in enumerate(folds): fold_ids[validation]=k
    pd.DataFrame({"source_row":train.source_row.to_numpy(),"fold_validacion":fold_ids}).to_csv(raiz/"datos/datos_limp/folds_v1.csv",index=False)
    manifest={"version":"preparacion_v1","revision_origen":lock["revision"],"sha256_original":lock["archivos"][lock["archivo_csv"]]["sha256"],
        "sha256_limpio":huella(raiz/"datos/datos_limp/tickets_clean_v1.csv"),"sha256_split":huella(raiz/"datos/datos_limp/split_v1.csv"),
        "sha256_folds":huella(raiz/"datos/datos_limp/folds_v1.csv"),"semilla":seed,"filas_train":len(train),"filas_test":len(test),
        "predictor":"text_clean","objetivo":"intent_clean","reglas":"Unicode NFKC, minúsculas, espacios, entidades comunes, vacíos/conflictos/duplicados excluidos",
        "sha256_fuentes":{n:huella(raiz/"fuentes"/n) for n in ["datos_prep.py","experimentos.py","train.py"]}}
    guardar(manifest,raiz/"datos/preparacion_v1.json")
    versiones={n:m.__version__ for n,m in [("numpy",np),("pandas",pd),("scikit-learn",sklearn),("scipy",scipy),("matplotlib",matplotlib),("mlflow",mlflow),("joblib",joblib)]}
    guardar({"python":platform.python_version(),"sistema":platform.system(),"paquetes":versiones},ev/"entorno.json")
    # EDA: comparar clases y longitudes, sin eliminar extremos por una regla arbitraria.
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10})
    colors=["#153A5B","#118A8A"]
    fig,ax=plt.subplots(figsize=(9,6))
    counts=clean.intent_clean.value_counts().sort_values()
    counts.plot.barh(ax=ax,color=colors[0]);ax.set_xlabel("Solicitudes después de deduplicar");ax.set_ylabel("")
    ax.tick_params(axis="y",labelsize=8);fig.tight_layout();fig.savefig(figs/"distribucion.png",dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,3.6))
    axes[0].hist(raw.instruction.str.len(),bins=35,alpha=.55,label="Original",color=colors[0])
    axes[0].hist(clean.text_clean.str.len(),bins=35,alpha=.55,label="Preparado",color=colors[1]);axes[0].legend()
    axes[0].set_xlabel("Caracteres");axes[0].set_ylabel("Frecuencia")
    axes[1].bar(["Conservados","Duplicados"],[len(clean),len(raw)-len(clean)],color=colors)
    axes[1].set_ylabel("Registros");fig.tight_layout();fig.savefig(figs/"calidad.png",dpi=180);plt.close(fig)
    tracking_dir.mkdir(parents=True,exist_ok=True)
    tracking_uri="sqlite:///"+(tracking_dir/"mlflow.db").as_posix()
    mlflow.set_tracking_uri(tracking_uri)
    artifacts=tracking_dir/"artefactos";artifacts.mkdir(exist_ok=True)
    experiment_name="Act5_GP_Entrenamiento_v1"
    experiment=mlflow.get_experiment_by_name(experiment_name)
    experiment_id=experiment.experiment_id if experiment else mlflow.create_experiment(experiment_name,artifact_location=artifacts.as_uri())
    base_commit=subprocess.check_output(["git","-C",str(raiz),"rev-parse","HEAD"],text=True).strip()
    specs={"MultinomialNB":(MultinomialNB(),{"tfidf__ngram_range":[(1,1),(1,2)],"clf__alpha":[.1,.5,1.]}),
           "LinearSVC":(LinearSVC(random_state=seed,max_iter=10000),{"tfidf__ngram_range":[(1,1),(1,2)],"clf__C":[.5,1.,2.]})}
    X,y=train.text_clean,train.intent_clean
    xt,yt=test.text_clean,test.intent_clean
    dummy=DummyClassifier(strategy="most_frequent").fit(np.zeros((len(y),1)),y)
    baseline=metricas(yt,dummy.predict(np.zeros((len(yt),1))))
    records=[];searches={};predictions={};scores={};models_best={}
    for name,(clf,params) in specs.items():
        print("Entrenando",name,flush=True)
        with mlflow.start_run(experiment_id=experiment_id,run_name=name) as run:
            mlflow.set_tags({"etapa":"entrenamiento","git_commit_base":base_commit,"dataset_revision":lock["revision"],"objetivo":"intent"})
            mlflow.log_params({"seed":seed,"cv_folds":5,"scoring":"f1_macro","min_df":2,"max_features":20000,"norm":"l2","sublinear_tf":True,
                "train_rows":len(train),"test_rows":len(test),"clean_sha256":manifest["sha256_limpio"],"split_sha256":manifest["sha256_split"],"codigo_sha256":manifest["sha256_fuentes"]["experimentos.py"]})
            pipe=Pipeline([("tfidf",TfidfVectorizer(min_df=2,max_features=20000,sublinear_tf=True,norm="l2")),("clf",clf)])
            grid=GridSearchCV(pipe,params,cv=folds,scoring={"f1_macro":"f1_macro","accuracy":"accuracy"},refit="f1_macro",n_jobs=2,return_train_score=True,error_score="raise")
            start=time.perf_counter();grid.fit(X,y);elapsed=time.perf_counter()-start
            cv_df=pd.DataFrame(grid.cv_results_);cv_df.to_csv(ev/(name+"_grid.csv"),index=False)
            for i,row in cv_df.iterrows():
                with mlflow.start_run(experiment_id=experiment_id,run_name=f"{name}_candidato_{i}",nested=True):
                    mlflow.log_params({k:str(v) for k,v in row["params"].items()})
                    mlflow.log_metrics({"cv_f1_media":row["mean_test_f1_macro"],"cv_f1_de":row["std_test_f1_macro"],"cv_accuracy":row["mean_test_accuracy"]})
                    for k in range(5):mlflow.log_metric(f"fold_{k}_f1",row[f"split{k}_test_f1_macro"])
            best=grid.best_estimator_;models_best[name]=best;searches[name]=grid
            # La selección utiliza exclusivamente validación, nunca las métricas de prueba.
            predictions[name]=best.predict(xt)
            score=best.predict_proba(xt) if name=="MultinomialNB" else best.decision_function(xt)
            classes=best.classes_;binary=label_binarize(yt,classes=classes)
            aucs=[roc_auc_score(binary[:,k],score[:,k]) for k in range(len(classes))]
            auc=float(np.mean(aucs));scores[name]=(binary,score)
            perclass=pd.DataFrame(classification_report(yt,predictions[name],output_dict=True,zero_division=0)).T
            perclass["roc_auc_ovr"] = pd.Series(dict(zip(classes,aucs)))
            perclass.to_csv(ev/(name+"_por_clase.csv"))
            trainmetrics=metricas(y,best.predict(X));testmetrics=metricas(yt,predictions[name])
            best.predict(xt.iloc[:5]);lat=[]
            for text in xt.iloc[:200]:
                t=time.perf_counter();best.predict([text]);lat.append((time.perf_counter()-t)*1000)
            model_path=models/(name+".joblib");joblib.dump(best,model_path)
            row={"modelo":name,"cv_f1_media":float(grid.best_score_),"cv_f1_de":float(cv_df.iloc[grid.best_index_].std_test_f1_macro),
                 **testmetrics,"roc_auc_macro_ovr":auc,"train_f1_macro":trainmetrics["f1_macro"],"busqueda_segundos":elapsed,
                 "latencia_p95_ms":float(np.percentile(lat,95)),"modelo_bytes":model_path.stat().st_size,
                 "run_id":run.info.run_id,"mejores_parametros":str(grid.best_params_)}
            mlflow.log_params({"best_"+k:str(v) for k,v in grid.best_params_.items()})
            mlflow.log_metrics({k:v for k,v in row.items() if isinstance(v,(float,int))})
            mlflow.log_dict(manifest,"preparacion_v1.json")
            for path in [ev/"calidad_datos.json",ev/"entorno.json",ev/(name+"_grid.csv"),ev/(name+"_por_clase.csv"),figs/"calidad.png",figs/"distribucion.png"]:mlflow.log_artifact(str(path))
            signature=mlflow.models.infer_signature(X.iloc[:3].to_numpy(),best.predict(X.iloc[:3]))
            info=mlflow.sklearn.log_model(best,name="model",signature=signature,input_example=X.iloc[:3].to_numpy())
            recovered=mlflow.sklearn.load_model(info.model_uri)
            assert np.array_equal(recovered.predict(xt),predictions[name])
            row["modelo_mlflow_recuperado"]=True;records.append(row)
    results=pd.DataFrame(records);results.to_csv(ev/"comparacion_modelos.csv",index=False)
    winner=results.sort_values(["cv_f1_media","modelo"],ascending=[False,True]).iloc[0].modelo
    names=list(specs);a=(predictions[names[0]]==yt.to_numpy()).astype(int);b=(predictions[names[1]]==yt.to_numpy()).astype(int)
    only_a=int(((a==1)&(b==0)).sum());only_b=int(((a==0)&(b==1)).sum())
    p=float(binomtest(only_a,only_a+only_b,p=.5).pvalue) if only_a+only_b else 1.
    rng=np.random.default_rng(seed);delta=a-b
    bootstrap=np.array([rng.choice(delta,len(delta),replace=True).mean() for _ in range(2000)])
    statistics={"comparacion":"MultinomialNB menos LinearSVC","diferencia_accuracy":float(delta.mean()),"ic95_inferior":float(np.percentile(bootstrap,2.5)),
        "ic95_superior":float(np.percentile(bootstrap,97.5)),"solo_nb_correcto":only_a,"solo_svm_correcto":only_b,"ambos_correctos":int(((a==1)&(b==1)).sum()),
        "ambos_incorrectos":int(((a==0)&(b==0)).sum()),"mcnemar_exacto_p":p,"bootstrap_iteraciones":2000,"nivel_significancia":.05}
    guardar(statistics,ev/"estadistica.json")
    pd.DataFrame({"source_row":test.source_row,"real":yt,**{n:predictions[n] for n in names}}).to_csv(ev/"predicciones_prueba.csv",index=False)
    errors=[]
    for name in names:
        err=pd.DataFrame({"real":yt.to_numpy(),"predicha":predictions[name]})
        err=err[err.real!=err.predicha].groupby(["real","predicha"]).size().sort_values(ascending=False).head(8)
        errors.extend({"modelo":name,"real":i[0],"predicha":i[1],"casos":int(v)} for i,v in err.items())
    pd.DataFrame(errors).to_csv(ev/"confusiones_principales.csv",index=False)
    fig,ax=plt.subplots(figsize=(6.8,4.2));roc_grid=np.linspace(0,1,1001)
    for name,color in zip(names,colors):
        binary,score=scores[name];tprs=[]
        for k in range(binary.shape[1]):
            fpr,tpr,_=roc_curve(binary[:,k],score[:,k]);tprs.append(np.interp(roc_grid,fpr,tpr))
        ax.plot(roc_grid,np.mean(tprs,axis=0),label=f"{name}: AUC macro={results.set_index('modelo').loc[name,'roc_auc_macro_ovr']:.5f}",color=color,lw=2)
    ax.plot([0,1],[0,1],"--",color="gray",label="Referencia aleatoria")
    ax.set(xlabel="Tasa de falsos positivos",ylabel="Sensibilidad",xlim=(0,1),ylim=(0,1.02));ax.legend(loc="lower right",fontsize=8)
    fig.tight_layout();fig.savefig(figs/"roc_macro.png",dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,3.4))
    for i,name in enumerate(names):
        r=results.set_index("modelo").loc[name]
        ax.errorbar(r.cv_f1_media,i,xerr=r.cv_f1_de,fmt="o",capsize=5,color=colors[i],label="CV media y DE" if i==0 else None)
        ax.scatter(r.f1_macro,i,marker="s",color="black",label="Prueba" if i==0 else None)
    ax.set_yticks(range(2),names);ax.set_xlabel("F1 macro (escala ampliada)");ax.set_xlim(.98,1.001);ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(figs/"comparacion.png",dpi=180);plt.close(fig)
    with mlflow.start_run(experiment_id=experiment_id,run_name="comparacion_estadistica"):
        mlflow.log_metrics({k:v for k,v in statistics.items() if isinstance(v,(float,int))})
        mlflow.log_artifacts(str(ev),artifact_path="evidencias")
    client=MlflowClient(tracking_uri=tracking_uri)
    runs=mlflow.search_runs(experiment_ids=[experiment_id],filter_string=f"attributes.start_time >= {inicio}")
    runs.to_csv(ev/"mlflow_runs.csv",index=False)
    assert len(runs)==15 and all(runs.status=="FINISHED")
    checks=[]
    for rec in records:
        run=client.get_run(rec["run_id"])
        artifact_paths=[a.path for a in client.list_artifacts(rec["run_id"])]
        assert run.info.status=="FINISHED" and "preparacion_v1.json" in artifact_paths
        assert run.data.metrics["f1_macro"]==rec["f1_macro"]
        checks.append({"modelo":rec["modelo"],"run_id":rec["run_id"],"estado":run.info.status,"parametros":run.data.params,"metricas":run.data.metrics,
                       "artefactos":artifact_paths,"modelo_recargado":True})
    guardar({"experimento":experiment_name,"ejecuciones_nuevas":15,"verificaciones":checks},ev/"mlflow_evidencia.json")
    summary={"fecha_utc":datetime.now(timezone.utc).isoformat(),"dataset":quality,"preparacion":manifest,"versiones":versiones,"baseline":baseline,
             "modelos":records,"recomendado_por_cv":winner,"estadistica":statistics,"mlflow_experimento":experiment_name,"mlflow_runs":15,"git_commit_base":base_commit}
    guardar(summary,ev/"resumen.json")
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
    return summary
