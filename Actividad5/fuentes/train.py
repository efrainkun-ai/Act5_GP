#!/usr/bin/env python3
"""Actividad 5 v3: entrenamiento reproducible y trazabilidad Git comprobada."""
import sys, subprocess, os
from pathlib import Path
IN_COLAB=False
TRAIN_SCRIPT=Path(__file__).read_text(encoding="utf-8")
from pathlib import Path
import re, json, hashlib, unicodedata, urllib.request, platform, time, shutil, uuid, importlib.util
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib, sklearn, scipy, mlflow, mlflow.sklearn, sqlalchemy, packaging
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, ConfusionMatrixDisplay, roc_auc_score, roc_curve
from scipy.stats import binomtest
from mlflow.tracking import MlflowClient
from IPython.display import display

GUARDAR_EN_DRIVE = True
if IN_COLAB and GUARDAR_EN_DRIVE:
    from google.colab import drive
    drive.mount('/content/drive')
    ROOT = Path('/content/drive/MyDrive/Act5_GP/Actividad5')
else:
    ROOT = Path(os.environ.get('ACT5_ROOT', str(Path.cwd() / 'Actividad5')))
ROOT = ROOT.resolve()
BATCH_ID = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '_' + uuid.uuid4().hex[:8]
RAW, PROCESSED, SOURCES = [ROOT / p for p in ['datos/datos_ini', 'datos/datos_limp', 'fuentes']]
REPORTS = ROOT/'evidencias'/BATCH_ID
MODELS = ROOT/'modelos'/BATCH_ID
TRACKING = ROOT/'.mlflow_local'
for p in [RAW, PROCESSED, SOURCES, REPORTS, MODELS, TRACKING]: p.mkdir(parents=True, exist_ok=True)
SEED = 42
np.random.seed(SEED)
def sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save_json(obj, path): Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
versions = {name: module.__version__ for name,module in [('numpy',np),('pandas',pd),('scikit-learn',sklearn),('scipy',scipy),('matplotlib',__import__('matplotlib')),('mlflow',mlflow),('joblib',joblib),('sqlalchemy',sqlalchemy),('packaging',packaging)]}
(ROOT/'requirements_effective.txt').write_text(''.join(f'{k}=={v}\n' for k,v in versions.items()))
save_json({'python':platform.python_version(),'platform':platform.platform(),'packages':versions}, REPORTS/'environment.json')
print('Directorio del proyecto:', ROOT)
display(pd.DataFrame(versions.items(), columns=['Paquete','Versión']))

# Guardar cada lote por separado impide mezclar evidencias de varias ejecuciones.
tracking_uri = 'sqlite:///' + str((TRACKING/'mlflow.db').resolve())
mlflow.set_tracking_uri(tracking_uri)
client = MlflowClient(tracking_uri=tracking_uri)
def set_experiment_local(name):
    exp = client.get_experiment_by_name(name)
    if exp is None:
        client.create_experiment(name, artifact_location=(TRACKING/'artefactos').as_uri())
    else:
        assert exp.lifecycle_stage == 'active', 'El experimento está eliminado. Restaura o elige otro nombre.'
        assert exp.artifact_location == (TRACKING/'artefactos').as_uri(), 'El almacén cambió de ruta: usa una raíz nueva o conserva la ubicación original.'
    mlflow.set_experiment(name)
    return client.get_experiment_by_name(name).experiment_id


# La referencia puede fijarse a un commit concreto para repetir una ejecución histórica.
GIT_URL='https://github.com/efrainkun-ai/Act5_GP.git'
CODE_REF=os.environ.get('ACT5_CODE_REF','origin/main')
CODE_DIR=Path(os.environ.get('ACT5_CODE_REPO', '/content/Act5_GP_codigo' if IN_COLAB else str(ROOT.parent/'Act5_GP_codigo')))
if not (CODE_DIR/'.git').is_dir():
    CODE_DIR.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['git','clone',GIT_URL,str(CODE_DIR)],check=True,timeout=180)
remote=subprocess.check_output(['git','-C',str(CODE_DIR),'remote','get-url','origin'],text=True).strip()
assert remote.removesuffix('.git')==GIT_URL.removesuffix('.git'),'Repositorio de código inesperado'
subprocess.run(['git','-C',str(CODE_DIR),'fetch','origin','main'],check=True,timeout=180)
CODE_COMMIT=subprocess.check_output(['git','-C',str(CODE_DIR),'rev-parse',CODE_REF],text=True).strip()
CODE_URL=f'https://github.com/efrainkun-ai/Act5_GP/commit/{CODE_COMMIT}'
REPO_TRAIN_PATH='Actividad5/fuentes/train.py'
versioned=subprocess.check_output(['git','-C',str(CODE_DIR),'show',f'{CODE_COMMIT}:{REPO_TRAIN_PATH}'])
assert versioned==TRAIN_SCRIPT.encode('utf-8'),'El notebook y el script del commit difieren. Descarga el notebook de la misma versión o fija ACT5_CODE_REF.'
(SOURCES/'train.py').write_text(TRAIN_SCRIPT,encoding='utf-8')
CODE_SHA=sha256(SOURCES/'train.py')
code_provenance={'git_commit':CODE_COMMIT,'commit_url':CODE_URL,'train_sha256':CODE_SHA,
 'train_url':f'https://github.com/efrainkun-ai/Act5_GP/blob/{CODE_COMMIT}/{REPO_TRAIN_PATH}',
 'code_verified_byte_for_byte':True}
save_json(code_provenance,REPORTS/'codigo_versionado.json')
print('Código versionado y verificado:',CODE_URL)
print('SHA-256 de train.py:',CODE_SHA)


REPO = 'bitext/Bitext-customer-support-llm-chatbot-training-dataset'
REVISION = '430d1a89bd93bd1fa23c16f29dd53e73f0087443'
CSV_NAME = 'Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.csv'
EXPECTED_SHA = '6f81102b0100b97b8468eb04368033a23206bf1fde9d53500d5806ec1001a434'
BASE_URL = f'https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/'
def download_verified(url, dest, expected=None):
    dest=Path(dest)
    if dest.exists():
        if expected and sha256(dest)!=expected:
            raise ValueError(f'Archivo alterado: {dest}. Conserva una copia y revisa su procedencia.')
        return
    temp=dest.with_suffix(dest.suffix+'.part')
    try:
        with urllib.request.urlopen(url,timeout=120) as response, temp.open('wb') as f:
            shutil.copyfileobj(response,f)
        if expected and sha256(temp)!=expected: raise ValueError('SHA-256 inesperado en descarga')
        temp.replace(dest)
    finally:
        temp.unlink(missing_ok=True)
download_verified(BASE_URL+CSV_NAME, RAW/CSV_NAME, EXPECTED_SHA)
download_verified(BASE_URL+'README.md', RAW/'README_fuente.md')
# La licencia se documenta por URL y declaración de la revisión fijada.
df_original = pd.read_csv(RAW/CSV_NAME, dtype=str)
assert set(df_original.columns)=={'instruction','intent','category','flags','response'}
assert len(df_original)==26872
print('Filas y columnas:',df_original.shape)
print('Intenciones:',df_original.intent.nunique(),'Categorías:',df_original.category.nunique())
display(df_original[['instruction','intent','category']].head())
display(df_original.isna().sum().to_frame('Faltantes'))
save_json({'dataset':REPO,'revision':REVISION,'url':BASE_URL+CSV_NAME,'sha256':EXPECTED_SHA,
           'source_card_sha256':sha256(RAW/'README_fuente.md'),'license':'CDLA Sharing 1.0',
           'license_url':'https://cdla.dev/sharing-1-0/'}, ROOT/'datos/dataset.lock.json')


CLEANING_SOURCE = "import pandas as pd\nimport re, unicodedata\n\ndef clean_text(value):\n    if pd.isna(value): return ''\n    text = unicodedata.normalize('NFKC', str(value)).strip().lower()\n    text = re.sub(r'\\{\\{.*?\\}\\}', ' entity ', text)\n    text = re.sub(r'[\\w.+-]+@[\\w.-]+\\.[a-z]{2,}', ' email ', text)\n    text = re.sub(r'(?<!\\w)\\+?\\d[\\d ()-]{7,}\\d(?!\\w)', ' phone ', text)\n    return re.sub(r'\\s+', ' ', text).strip()\n\n"
(SOURCES/'datos_prep.py').write_text(CLEANING_SOURCE,encoding='utf-8')
spec = importlib.util.spec_from_file_location("act5_datos_prep", SOURCES/"datos_prep.py")
prep_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep_module)
clean_text = prep_module.clean_text

audit = df_original.copy()
audit.insert(0, 'source_row', np.arange(len(audit)))
audit['text_clean'] = audit.instruction.map(clean_text)
audit['intent_clean'] = audit.intent.fillna('').str.strip().str.lower()
audit['text_sha256'] = audit.text_clean.map(lambda s: hashlib.sha256(s.encode()).hexdigest())
audit['exclusion_reason'] = ''
invalid = audit.text_clean.eq('') | audit.intent_clean.eq('') | audit.category.fillna('').str.strip().eq('')
audit.loc[invalid,'exclusion_reason'] = 'texto_o_etiqueta_vacios'
valid = audit.loc[~invalid]
conflicts = valid.groupby('text_sha256').intent_clean.nunique()
conflict_keys = set(conflicts[conflicts>1].index)
audit.loc[~invalid & audit.text_sha256.isin(conflict_keys),'exclusion_reason'] = 'etiquetas_contradictorias'
eligible = audit.exclusion_reason.eq('')
duplicates = audit.loc[eligible].duplicated('text_sha256', keep='first')
audit.loc[duplicates[duplicates].index,'exclusion_reason'] = 'texto_duplicado'
clean = audit.loc[audit.exclusion_reason.eq(''), ['source_row','text_clean','text_sha256','intent_clean','category','flags']].copy()
assert not clean.text_sha256.duplicated().any()
assert clean.groupby('intent_clean').category.nunique().max()==1
assert clean.intent_clean.value_counts().min()>=10
clean.to_csv(PROCESSED/'tickets_clean_v1.csv', index=False)
# Auditoría completa: incluye registros conservados y descartados.
audit[['source_row','text_sha256','intent_clean','exclusion_reason']].to_csv(REPORTS/'audit_all_rows.csv',index=False)
quality = {'raw_rows':len(audit),'clean_rows':len(clean),'excluded_rows':len(audit)-len(clean),
           'exclusion_reasons':audit.exclusion_reason.replace('','conservado').value_counts().to_dict(),
           'intents':int(clean.intent_clean.nunique()),'categories':int(clean.category.nunique()),
           'missing_raw':df_original.isna().sum().astype(int).to_dict(),
           'empty_raw':{c:int(df_original[c].fillna('').str.strip().eq('').sum()) for c in df_original},
           'conflicting_texts':len(conflict_keys)}
audit[['source_row','text_sha256','intent_clean','exclusion_reason']].to_csv(PROCESSED/'auditoria_v1.csv',index=False)
save_json(quality,REPORTS/'quality.json')
display(pd.DataFrame(quality['exclusion_reasons'].items(),columns=['Estado','Filas']))
print('Filas limpias:',len(clean))


fig, axes = plt.subplots(1,3,figsize=(18,6))
clean.intent_clean.value_counts().sort_values().plot.barh(ax=axes[0],fontsize=7)
axes[0].set_title('Distribución de intenciones'); axes[0].set_xlabel('Solicitudes')
audit.text_clean.str.len().hist(bins=40,ax=axes[1],alpha=.55,label='Original normalizado')
clean.text_clean.str.len().hist(bins=40,ax=axes[1],alpha=.55,label='Después de deduplicar')
axes[1].set_title('Longitud del texto'); axes[1].set_xlabel('Caracteres'); axes[1].legend()
pd.Series(quality['exclusion_reasons']).plot.bar(ax=axes[2],rot=30)
axes[2].set_title('Estado de los registros'); axes[2].set_ylabel('Filas')
fig.tight_layout(); fig.savefig(REPORTS/'quality.png',dpi=160,bbox_inches='tight'); plt.show()
counts = clean.intent_clean.value_counts()
print(f'Desbalance máximo/mínimo después de limpiar: {counts.max()/counts.min():.2f}.')
print('Las exclusiones reducen redundancia exacta; no demuestran diversidad de plantillas ni cobertura real del negocio.')
display(clean.assign(characters=clean.text_clean.str.len()).nlargest(5,'characters')[['text_clean','intent_clean','characters']])


train, test = train_test_split(clean,test_size=.2,random_state=SEED,stratify=clean.intent_clean)
assert set(train.text_sha256).isdisjoint(set(test.text_sha256))
split = pd.concat([train.assign(split='train'),test.assign(split='test')])[['source_row','text_sha256','split']]
split.to_csv(PROCESSED/'split_v1.csv',index=False)
X_train, y_train = train.text_clean, train.intent_clean
X_test, y_test = test.text_clean, test.intent_clean
folds=list(StratifiedKFold(n_splits=5,shuffle=True,random_state=SEED).split(X_train,y_train))
fold_rows=[]
for fold,(fit_idx,val_idx) in enumerate(folds):
    assert set(train.iloc[fit_idx].text_sha256).isdisjoint(set(train.iloc[val_idx].text_sha256))
    fold_rows.append(pd.DataFrame({'source_row':train.iloc[val_idx].source_row.to_numpy(),
        'text_sha256':train.iloc[val_idx].text_sha256.to_numpy(),'validation_fold':fold}))
fold_manifest=pd.concat(fold_rows,ignore_index=True)
assert len(fold_manifest)==len(train) and not fold_manifest.source_row.duplicated().any()
fold_manifest.to_csv(PROCESSED/'folds_v1.csv',index=False)
manifest={'dataset':REPO,'revision':REVISION,'license':'cdla-sharing-1.0','raw_sha256':EXPECTED_SHA,
 'processed_sha256':sha256(PROCESSED/'tickets_clean_v1.csv'),'split_sha256':sha256(PROCESSED/'split_v1.csv'),
 'folds_sha256':sha256(PROCESSED/'folds_v1.csv'),'cleaning_code_sha256':sha256(SOURCES/'datos_prep.py'),
 'seed':SEED,'test_size':.2,'cleaning_version':'v1','target':'intent_clean','predictor':'text_clean',
 'train_rows':len(train),'test_rows':len(test),'folds':5}
save_json(manifest,ROOT/'datos/preparacion_v1.json')
save_json(manifest,REPORTS/'dataset_manifest_v1.json')
git_commit=CODE_COMMIT
clean_versioned=subprocess.check_output(['git','-C',str(CODE_DIR),'show',f'{CODE_COMMIT}:Actividad5/fuentes/datos_prep.py'])
assert clean_versioned==(SOURCES/'datos_prep.py').read_bytes(),'Limpieza distinta del código publicado'
manifest.update({'git_commit':CODE_COMMIT,'commit_url':CODE_URL,'train_code_sha256':CODE_SHA})
save_json(manifest,ROOT/'datos/preparacion_v1.json')
save_json(manifest,REPORTS/'dataset_manifest_v1.json')
save_json({'git_commit_observado':git_commit,'batch_id':BATCH_ID,'manifest':manifest,
           'source_verified':True},REPORTS/'provenance.json')
print('Train:',len(train),'Test:',len(test),'Folds:',len(folds),'Commit:',git_commit)
print('Código, limpieza y particiones verificados.')


set_experiment_local('Act5_GP_Configuracion_Integrado')
control_file=REPORTS/'mlflow_control.txt'
control_file.write_text('Actividad 5: verificación de persistencia de MLflow.\n',encoding='utf-8')
with mlflow.start_run(run_name='verificacion_'+BATCH_ID) as control_run:
    mlflow.set_tags({'batch_id':BATCH_ID,'kind':'configuration','git_commit':CODE_COMMIT})
    mlflow.log_param('proyecto','AI-SupportAssist')
    mlflow.log_metric('valor_control',1.0)
    mlflow.log_artifact(str(control_file))
    mlflow.log_artifact(str(REPORTS/'environment.json'))
control=client.get_run(control_run.info.run_id)
download_dir=REPORTS/'descargas_verificadas'
download_dir.mkdir(exist_ok=True)
control_download=client.download_artifacts(control.info.run_id,'mlflow_control.txt',str(download_dir))
controls={'finished':control.info.status=='FINISHED','parametro':control.data.params.get('proyecto')=='AI-SupportAssist',
          'metrica':control.data.metrics.get('valor_control')==1.0,'artefacto':sha256(control_download)==sha256(control_file)}
assert all(controls.values()),controls
save_json({'run_id':control.info.run_id,'controles':controls},REPORTS/'mlflow_configuracion.json')
print('MLflow configurado y persistencia validada:',controls)


scoring={'f1_macro':'f1_macro','accuracy':'accuracy'}
specs = {
 'MultinomialNB':(MultinomialNB(),{'tfidf__ngram_range':[(1,1),(1,2)],'clf__alpha':[.1,.5,1.]}),
 'LinearSVC':(LinearSVC(random_state=SEED,max_iter=10000),{'tfidf__ngram_range':[(1,1),(1,2)],'clf__C':[.5,1.,2.]})}
experiment_name='Actividad5_AI_SupportAssist_Intent_v3'
EXPERIMENT_ID=set_experiment_local(experiment_name)
model_uris={}
scores_by_model={}
def metrics(y,p):
    return {'accuracy':accuracy_score(y,p),'precision_macro':precision_score(y,p,average='macro',zero_division=0),
            'recall_macro':recall_score(y,p,average='macro',zero_division=0),'f1_macro':f1_score(y,p,average='macro',zero_division=0)}
dummy=DummyClassifier(strategy='most_frequent').fit(np.zeros((len(y_train),1)),y_train)
baseline=metrics(y_test,dummy.predict(np.zeros((len(y_test),1))))
save_json(baseline,REPORTS/'baseline.json')
searches, predictions, records = {}, {}, []
best_configs=[]
for name,(clf,grid_params) in specs.items():
    print('Entrenando:',name,flush=True)
    pipe=Pipeline([('tfidf',TfidfVectorizer(min_df=2,max_features=20000,sublinear_tf=True)),('clf',clf)])
    with mlflow.start_run(run_name=name) as run:
        mlflow.set_tags({'batch_id':BATCH_ID,'kind':'model','git_commit':CODE_COMMIT})
        mlflow.set_tags({'dataset_revision':REVISION,'git_commit':git_commit,'cleaning_version':'v1','scope':'synthetic_english_prototype'})
        mlflow.log_params({'seed':SEED,'folds':5,'selection_metric':'f1_macro','dataset_sha256':manifest['processed_sha256'],
                           'split_sha256':manifest['split_sha256'],'folds_sha256':manifest['folds_sha256'],'train_rows':len(train),'test_rows':len(test),'max_features':20000,'min_df':2})
        start=time.perf_counter()
        grid=GridSearchCV(pipe,grid_params,cv=folds,scoring=scoring,refit='f1_macro',n_jobs=1,return_train_score=True,error_score='raise')
        grid.fit(X_train,y_train)
        fit_seconds=time.perf_counter()-start
        cv_results=pd.DataFrame(grid.cv_results_)
        cv_results.to_csv(REPORTS/f'{name}_grid.csv',index=False)
        for idx,row in cv_results.iterrows():
            with mlflow.start_run(run_name=f'{name}_candidate_{idx}',nested=True):
                mlflow.set_tags({'batch_id':BATCH_ID,'kind':'candidate','git_commit':CODE_COMMIT})
                mlflow.log_params({k:str(v) for k,v in row['params'].items()})
                mlflow.log_metrics({'cv_f1_macro_mean':row['mean_test_f1_macro'],'cv_f1_macro_std':row['std_test_f1_macro'],
                                    'cv_accuracy_mean':row['mean_test_accuracy'],'mean_fit_seconds':row['mean_fit_time']})
                for fold in range(5): mlflow.log_metric(f'fold_{fold}_f1_macro',row[f'split{fold}_test_f1_macro'])
        best=grid.best_estimator_
        pred=best.predict(X_test)
        predictions[name]=pred
        classes=best.named_steps['clf'].classes_
        assert set(classes)==set(y_test.unique())
        scores=best.predict_proba(X_test) if hasattr(best,'predict_proba') else best.decision_function(X_test)
        assert scores.shape==(len(y_test),len(classes))
        aucs=[roc_auc_score((y_test.to_numpy()==label).astype(int),scores[:,j]) for j,label in enumerate(classes)]
        scores_by_model[name]=(classes,scores)
        pd.DataFrame({'intent':classes,'roc_auc_ovr':aucs}).to_csv(REPORTS/f'{name}_auc_por_clase.csv',index=False)
        train_metrics=metrics(y_train,best.predict(X_train)); test_metrics=metrics(y_test,pred)
        test_metrics['roc_auc_macro_ovr']=float(np.mean(aucs))
        # Latencia por solicitud tras calentamiento; depende del hardware y no incluye red ni CRM.
        samples=X_test.iloc[:min(200,len(X_test))].tolist(); best.predict(samples[:5])
        lat=[]
        for text in samples:
            start=time.perf_counter(); best.predict([text]);lat.append((time.perf_counter()-start)*1000)
        row={'model':name,'cv_f1_mean':grid.best_score_,'cv_f1_std':float(cv_results.iloc[grid.best_index_]['std_test_f1_macro']),
             **{'test_'+k:v for k,v in test_metrics.items()},'train_f1_macro':train_metrics['f1_macro'],
             'search_seconds':fit_seconds,'latency_p50_ms':float(np.median(lat)),'latency_p95_ms':float(np.percentile(lat,95)),
             'run_id':run.info.run_id,'best_params':str(grid.best_params_)}
        mlflow.log_params({'best_'+k:str(v) for k,v in grid.best_params_.items()})
        selected_config={'model':name,**{k:(list(v) if isinstance(v,tuple) else v) for k,v in grid.best_params_.items()},
            'cv_f1_macro':float(grid.best_score_),'cv_f1_std':float(cv_results.iloc[grid.best_index_]['std_test_f1_macro']),
            'best_index':int(grid.best_index_),'git_commit':CODE_COMMIT}
        save_json(selected_config,REPORTS/f'{name}_best_params.json')
        mlflow.log_dict(selected_config,'best_params.json')
        mlflow.log_artifact(str(REPORTS/'codigo_versionado.json'))
        best_configs.append(selected_config)
        mlflow.log_metrics({k:v for k,v in row.items() if isinstance(v,(int,float))})
        mlflow.log_dict(manifest,'dataset_manifest.json')
        mlflow.log_artifact(str(REPORTS/f'{name}_grid.csv'))
        mlflow.log_artifact(str(REPORTS/'quality.json'))
        mlflow.log_artifact(str(REPORTS/'quality.png'))
        signature=mlflow.models.infer_signature(X_train.iloc[:3].to_numpy(),best.predict(X_train.iloc[:3]))
        model_info=mlflow.sklearn.log_model(best,name='model',signature=signature,input_example=X_train.iloc[:3].to_numpy())
        model_uris[name]=model_info.model_uri
        row['model_uri']=model_info.model_uri
        joblib.dump(best,MODELS/f'{name}.joblib')
        row['model_bytes']=(MODELS/f'{name}.joblib').stat().st_size
        mlflow.log_metric('model_bytes',row['model_bytes'])
        pd.DataFrame(classification_report(y_test,pred,output_dict=True,zero_division=0)).T.to_csv(REPORTS/f'{name}_classification_report.csv')
        for file in [f'{name}_classification_report.csv',f'{name}_auc_por_clase.csv','environment.json']:
            mlflow.log_artifact(str(REPORTS/file))
        mlflow.log_artifact(str(SOURCES/'datos_prep.py'),artifact_path='fuentes')
        records.append(row); searches[name]=grid
results=pd.DataFrame(records)
results.to_csv(REPORTS/'model_comparison.csv',index=False)
display(results.drop(columns=['run_id','best_params','model_uri']))
print('Baseline de clase mayoritaria:',baseline)

best_table=pd.DataFrame(best_configs)
best_table.to_csv(REPORTS/'mejores_hiperparametros.csv',index=False)
save_json(best_configs,REPORTS/'mejores_hiperparametros.json')
display(best_table[['model','clf__alpha','clf__C','tfidf__ngram_range','cv_f1_macro','cv_f1_std']])
for config in best_configs:
    parameter='clf__alpha' if config['model']=='MultinomialNB' else 'clf__C'
    print(config['model'],parameter,config[parameter],'n-gramas',config['tfidf__ngram_range'],
          'seleccionados por máximo F1 macro de CV:',round(config['cv_f1_macro'],6))
print('alpha controla el suavizado; C controla la penalización de errores. Los bigramas añaden contexto de dos palabras.')
print('La elección se fundamenta en la comparación de los seis candidatos con los mismos folds, sin usar la prueba para escoger parámetros.')


winner = results.sort_values(['cv_f1_mean','model'],ascending=[False,True]).iloc[0]['model']
labels=sorted(y_test.unique())
fig,axes=plt.subplots(1,2,figsize=(20,9))
for ax,name in zip(axes,specs):
    ConfusionMatrixDisplay.from_predictions(y_test,predictions[name],labels=labels,normalize='true',
        ax=ax,xticks_rotation=90,include_values=False,colorbar=False,cmap='Blues')
    ax.set_title(name+' — normalización por clase real');ax.tick_params(labelsize=6)
fig.tight_layout();fig.savefig(REPORTS/'confusion_matrices.png',dpi=160,bbox_inches='tight');plt.show()
fig,axes=plt.subplots(1,2,figsize=(11,4))
axes[0].bar(results.model,results.cv_f1_mean,yerr=results.cv_f1_std,capsize=5,label='CV media ± DE')
axes[0].scatter(results.model,results.test_f1_macro,color='black',label='Prueba');axes[0].set_ylim(0,1.05)
axes[0].set_ylabel('F1 macro');axes[0].legend()
axes[1].bar(results.model,results.latency_p95_ms);axes[1].set_ylabel('Latencia p95 (ms/solicitud)')
fig.tight_layout();fig.savefig(REPORTS/'comparison.png',dpi=160);plt.show()
errors=test[['source_row','text_clean','intent_clean','category']].copy()
for name in specs:errors['prediction_'+name]=predictions[name]
errors=errors.loc[np.logical_or.reduce([predictions[name]!=y_test.to_numpy() for name in specs])]
errors.to_csv(REPORTS/'errors.csv',index=False)
print('Modelo recomendado por CV:',winner)
print('Casos con algún error:',len(errors));display(errors.head(10))
for name in specs:
    wrong=errors.loc[errors['prediction_'+name]!=errors.intent_clean]
    print('Confusiones más frecuentes de',name)
    display(wrong.groupby(['intent_clean','prediction_'+name]).size().sort_values(ascending=False).head(5).to_frame('Casos'))

fig,ax=plt.subplots(figsize=(7,5))
for name,(classes,scores) in scores_by_model.items():
    grid_fpr=np.linspace(0,1,1001); tprs=[]
    for j,label in enumerate(classes):
        fpr,tpr,_=roc_curve((y_test.to_numpy()==label).astype(int),scores[:,j])
        tprs.append(np.interp(grid_fpr,fpr,tpr))
    mean_tpr=np.mean(tprs,axis=0);mean_tpr[0]=0;mean_tpr[-1]=1
    auc_value=results.set_index('model').loc[name,'test_roc_auc_macro_ovr']
    ax.plot(grid_fpr,mean_tpr,label=f'{name}: AUC macro {auc_value:.6f}')
ax.plot([0,1],[0,1],'--',color='grey',label='Referencia aleatoria')
ax.set(xlabel='Tasa de falsos positivos',ylabel='Sensibilidad',title='ROC media interpolada, uno contra el resto')
ax.legend();fig.tight_layout();fig.savefig(REPORTS/'roc_macro.png',dpi=160);plt.show()
print('AUC macro = media de las 27 AUC binarias; la curva es una interpolación visual.')
print('SVM usa márgenes sin convertirlos en probabilidades; Naive Bayes usa predict_proba.')


names=list(specs)
a=(predictions[names[0]]==y_test.to_numpy()).astype(int)
b=(predictions[names[1]]==y_test.to_numpy()).astype(int)
only_a=int(((a==1)&(b==0)).sum());only_b=int(((a==0)&(b==1)).sum())
p_value=float(binomtest(only_a,only_a+only_b,p=.5).pvalue) if only_a+only_b else 1.
rng=np.random.default_rng(SEED)
delta=a-b
boot=np.array([rng.choice(delta,size=len(delta),replace=True).mean() for _ in range(2000)])
stats={'comparison':names[0]+' menos '+names[1],'accuracy_difference':float(delta.mean()),
       'bootstrap_95_low':float(np.percentile(boot,2.5)),'bootstrap_95_high':float(np.percentile(boot,97.5)),
       'only_first_correct':only_a,'only_second_correct':only_b,'mcnemar_exact_p':p_value,
       'interpretation':'Exploratorio; datos sintéticos, posible dependencia entre paráfrasis.'}
save_json(stats,REPORTS/'statistics.json');display(pd.DataFrame([stats]))
print(f'McNemar exacta: p={p_value:.4f}. '+('No se rechaza igualdad de exactitud al nivel del 5 %.' if p_value>=.05 else 'Se rechaza igualdad de exactitud al nivel del 5 %, bajo los supuestos de la prueba.'))
print('Esta comparación evalúa exactitud, mientras que la selección del modelo utiliza F1 macro de validación.')
with mlflow.start_run(run_name='comparacion_estadistica') as comparison_run:
    mlflow.set_tags({'batch_id':BATCH_ID,'kind':'comparison','git_commit':CODE_COMMIT})
    mlflow.log_metrics({k:v for k,v in stats.items() if isinstance(v,(int,float))})
    mlflow.log_dict(stats,'statistics.json')
    mlflow.log_artifact(str(REPORTS/'model_comparison.csv'))
    for name in ['confusion_matrices.png','comparison.png','errors.csv','roc_macro.png','environment.json','provenance.json']:mlflow.log_artifact(str(REPORTS/name))

with mlflow.start_run(run_id=comparison_run.info.run_id):
    mlflow.log_artifact(str(REPORTS/'mejores_hiperparametros.csv'))
    mlflow.log_artifact(str(REPORTS/'mejores_hiperparametros.json'))
    mlflow.log_artifact(str(REPORTS/'codigo_versionado.json'))


selected=results.set_index('model').loc[winner]
conclusion=(f'El modelo seleccionado por validación cruzada fue {winner}, con F1 macro promedio '
 f'{selected.cv_f1_mean:.4f} y desviación estándar {selected.cv_f1_std:.4f}. En el conjunto de prueba obtuvo '
 f'F1 macro {selected.test_f1_macro:.4f} y exactitud {selected.test_accuracy:.4f}. '
 f'La preparación conservó {len(clean):,} solicitudes de {len(df_original):,} originales. '
 f'La prueba exploratoria de McNemar obtuvo p={p_value:.4f}; '
 + ('no se detectó una diferencia de exactitud concluyente al nivel del 5 %. ' if p_value>=.05 else 'se detectó una diferencia de exactitud al nivel del 5 %, condicionada a los supuestos de independencia. ')
 +
 'La recomendación se limita al prototipo de intenciones en inglés. No demuestra la meta de enrutamiento de NovaMarket '
 'ni los ahorros financieros de fase 1. Se requiere validación externa en español, revisión por intención y controles '
 'de datos personales antes de considerar su operación.')
print(conclusion)
(REPORTS/'conclusion.md').write_text('# Conclusión experimental\n\n'+conclusion,encoding='utf-8')
summary={'recommended_model':winner,'quality':quality,'statistics':stats,'models':records,'baseline':baseline}
save_json(summary,REPORTS/'summary.json')


expected_ids=[r['run_id'] for r in records]+[comparison_run.info.run_id]
runs=mlflow.search_runs(experiment_ids=[EXPERIMENT_ID],filter_string=f"tags.batch_id = '{BATCH_ID}'",max_results=100)
assert len(runs)==15 and set(expected_ids)<=set(runs.run_id)
assert (runs.status=='FINISHED').all()
assert (runs['tags.kind']=='candidate').sum()==12
runs.to_csv(REPORTS/'mlflow_runs.csv',index=False)
checks=[]
for record in records:
    name=record['model']; persisted=client.get_run(record['run_id'])
    assert persisted.data.tags['git_commit']==CODE_COMMIT
    assert persisted.data.params['dataset_sha256']==manifest['processed_sha256']
    assert persisted.data.params['folds_sha256']==manifest['folds_sha256']
    for metric in ['accuracy','precision_macro','recall_macro','f1_macro','roc_auc_macro_ovr']:
        assert np.isclose(persisted.data.metrics['test_'+metric],record['test_'+metric],rtol=0,atol=1e-12)
    downloaded=client.download_artifacts(record['run_id'],f'{name}_grid.csv',str(download_dir))
    assert sha256(downloaded)==sha256(REPORTS/f'{name}_grid.csv')
    restored=mlflow.sklearn.load_model(model_uris[name])
    assert np.array_equal(restored.predict(X_test),predictions[name])
    local=joblib.load(MODELS/f'{name}.joblib')
    assert np.array_equal(local.predict(X_test),predictions[name])
    checks.append({'model':name,'run_id':record['run_id'],'model_uri':model_uris[name],
        'status':persisted.info.status,'params':dict(persisted.data.params),'metrics':dict(persisted.data.metrics),
        'artifacts':[a.path for a in client.list_artifacts(record['run_id'])],
        'downloaded_grid_sha256':sha256(downloaded),'mlflow_predictions_equal':True,'joblib_predictions_equal':True})
evidence={'batch_id':BATCH_ID,'experiment_id':EXPERIMENT_ID,'training_runs':15,'git_commit':CODE_COMMIT,'commit_url':CODE_URL,'code_verified':True,
          'configuration_run':control.info.run_id,'models':checks,'all_runs_finished':True,'best_hyperparameters':best_configs}
save_json(evidence,REPORTS/'mlflow_verificacion.json')
with mlflow.start_run(run_id=comparison_run.info.run_id):
    mlflow.log_artifact(str(REPORTS/'mlflow_verificacion.json'))
    mlflow.log_artifact(str(REPORTS/'mlflow_runs.csv'))
display(runs[['run_id','status','tags.mlflow.runName','tags.kind']])
print('VERIFICACIÓN COMPLETA: 15 runs de entrenamiento/comparación y ambos modelos recuperados desde MLflow.')
# Inferencia de demostración en el mismo idioma. No es una evaluación adicional.
texts=['I want to cancel my order','How can I get my invoice?','Where is my refund?']
selected_model=mlflow.sklearn.load_model(model_uris[winner])
intent_to_category=clean.groupby('intent_clean').category.first().to_dict()
intent_pred=selected_model.predict([clean_text(t) for t in texts])
display(pd.DataFrame({'solicitud':texts,'intencion':intent_pred,
                      'categoria':[intent_to_category[i] for i in intent_pred]}))

assert (runs['tags.git_commit']==CODE_COMMIT).all()
print('Los 15 runs están vinculados al commit verificado:',CODE_URL)
