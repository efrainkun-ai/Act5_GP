"""Comprueba el recorrido frontend -> fetch -> API -> resultado con Chromium."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    out = Path('evidence'); out.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1440, 'height': 1100})
        failures = []
        page.on('pageerror', lambda error: failures.append(str(error)))
        page.goto(args.base_url)
        page.get_by_role('button', name='Reembolso', exact=True).click()
        with page.expect_response('**/api/v1/predict') as response:
            page.get_by_role('button', name='Analizar solicitud').click()
        assert response.value.status == 200
        expect(page.locator('#route')).to_have_text('Atención financiera humana')
        page.screenshot(path=str(out/'frontend-financiero.png'), full_page=True)
        page.get_by_role('button', name='Acceso a cuenta', exact=True).click()
        page.get_by_role('button', name='Analizar solicitud').click()
        expect(page.locator('#route')).to_have_text('Otra ruta de soporte')
        page.select_option('#language', 'es')
        page.fill('#text', 'Quiero un reembolso')
        page.get_by_role('button', name='Analizar solicitud').click()
        expect(page.locator('#error')).to_be_visible()
        expect(page.locator('#error-message')).to_contain_text('inglés')
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        page.screenshot(path=str(out/'frontend-movil.png'), full_page=True)
        assert not failures, failures
        browser.close()
    result = {'executed_at_utc': datetime.now(timezone.utc).isoformat(), 'browser': 'Chromium',
              'financial_route': True, 'other_route': True, 'spanish_review': True,
              'mobile_without_horizontal_overflow': True, 'javascript_errors': failures}
    (out/'browser.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
