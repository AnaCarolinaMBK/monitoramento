

import requests
import sys 
import json
import os 
from datetime import datetime
from PyQt5.QtCore import QUrl
from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton,QMessageBox, QComboBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from folium.plugins import MousePosition
import folium 
import threading
import websocket


usuarios = {}
navios ={}



#Funçoes

def abrirLogin():
    telalogin.show()


def abrirJaCadstrado():
    telaJaCadastrado.show()

def abrirEndereco(event):
    telaEndereco.show() 

def abrirTelaNavios():
    telaNavio.show()  


API_KEY = "5d8e5ade42174e3c14615a20bb089674d2a5c68e"


def on_message(ws, message):

    data = json.loads(message)

    if "Message" not in data:
        return

    msg = data["Message"]

    # Posicao 

    if "PositionReport" in msg:

        pr = msg["PositionReport"]

        mmsi = str(pr["UserID"])

        if mmsi not in navios:  
            navios[mmsi] = {}

        navios[mmsi]["lat"] = pr.get("Latitude")
        navios[mmsi]["lon"] = pr.get("Longitude")
        navios[mmsi]["velocidade"] = pr.get("Sog")


    # Dados estaticos do navio
    if "ShipStaticData" in msg:

        sd = msg["ShipStaticData"]

        mmsi = str(sd["UserID"])

        if mmsi not in navios:
            navios[mmsi] = {}

        navios[mmsi]["nome"] = sd.get("Name")
        navios[mmsi]["destino"] = sd.get("Destination")
        navios[mmsi]["tipo"] = (sd.get("ShipType"))

def on_open(ws):

    print ("CONECTADO")

    sub = {
        "APIKey": API_KEY,
        "BoundingBoxes": [[[ -90, -180 ], [ 90, 180 ]]],
        "FilterMessageTypes": ["PositionReport", "ShipStaticData"]
    }

    ws.send(json.dumps(sub))


def iniciar_websocket():

    ws = websocket.WebSocketApp(
        "wss://stream.aisstream.io/v0/stream",
        on_open=on_open,
        on_message=on_message
    )

    

    ws.run_forever()

def gerarMapaNavio():


    mapa = folium.Map(location=[-15,-45], zoom_start=4)

    formatter = "function(num) {return L.Util.formatNum(num, 5);};"

    MousePosition(
    position="bottomright",
    separator=" | ",
    prefix="Coordenadas:",
    lat_formatter=formatter,
    lng_formatter=formatter,).add_to(mapa)
    mapa.add_child(folium.LatLngPopup())
    



    for mmsi, dados in list (navios.items()):

        lat = dados.get("lat")
        lon = dados.get("lon")

        if lat is None or lon is None or "tipo" not in dados:
         continue
        
        
        nome = dados.get("nome", "Desconhecido")
        destino = dados.get("destino", "Não informado")
        vel = dados.get("velocidade", 0)
        tipo_codigo = dados.get("tipo")
        tipo = traduzir_tipo_navio(tipo_codigo)
        
        cor = "blue"
        icone = "ship"

        if tipo == "Cargueiro":
         cor = "green"
         icone = "ship"

        elif tipo == "Rebocador":
         cor = "darkblue"
         icone = "anchor"

        elif tipo == "Veleiro":
         cor = "cadetblue"
         icone = "flag"

        elif tipo == "Lazer":
         cor = "lightblue"

        elif tipo == "Passageiros":
         cor = "purple"
         icone = "ferry"

        elif tipo == "Petroleiro":
         cor = "red"
         icone = "oil-can"

        elif tipo == "Pesca":
         cor = "orange"
         icone = "fish"

        elif tipo == "Especial":
         cor = "gray"
         icone = "cog"


        imagem_url = f"https://photos.marinetraffic.com/ais/showphoto.aspx?mmsi={mmsi}"

        texto = f"""
        <div style="width:250px">

        <h4>{nome}</h4>

        <img src="{imagem_url}" width="230"><br><br>

        <b>MMSI:</b> {mmsi}<br>
        <b>Tipo:</b> {tipo}<br>
        <b>Destino:</b> {destino}<br>
        <b>Velocidade:</b> {vel} nós

        </div>
        """
      
        
     
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(texto, max_width=300),
            tooltip=f"{nome} | {destino}",
            icon=folium.Icon(color=cor, icon=icone, prefix="fa")
        ).add_to(mapa)

    mapa.save("mapa_navio.html")




def atualizarMapaNavio():

    gerarMapaNavio()

    caminho = os.path.abspath("mapa_navio.html")

    browser.load(QUrl.fromLocalFile(caminho))

def traduzir_tipo_navio(codigo):

    if not codigo:
        return "Sem informação"

    try:
        codigo = int(codigo)
    except:
        return "Sem informação"

    if codigo == 30:
        return "Pesca"

    elif codigo in [31, 32, 52]:
        return "Rebocador"

    elif codigo == 36:
        return "Veleiro"

    elif codigo == 37:
        return "Lazer"

    elif 60 <= codigo <= 69:
        return "Passageiros"

    elif 70 <= codigo <= 79:
        return "Cargueiro"

    elif 80 <= codigo <= 89:
        return "Petroleiro"

    elif 30 <= codigo <= 39:
        return "Especial"

    else:
        return "Outro"
    

    # ---------------- AVIÕES ----------------

def gerarMapaAvioes():

    mapa = folium.Map(location=[-15,-45], zoom_start=4)

    url = "https://opensky-network.org/api/states/all"

    formatter = "function(num) {return L.Util.formatNum(num, 5);};"

    MousePosition(
        position="bottomright",
        separator=" | ",
        prefix="Coordenadas:",
        lat_formatter=formatter,
        lng_formatter=formatter,
    ).add_to(mapa)

    mapa.add_child(folium.LatLngPopup())


    try:

        resposta = requests.get(url)
        dados = resposta.json()

        for aviao in dados["states"][:300]:

            callsign = aviao[1]
            lon = aviao[5]
            lat = aviao[6]
            velocidade = aviao[9]


            imagem_aviao = "https://upload.wikimedia.org/wikipedia/commons/5/5f/Airplane_silhouette.png"

            texto = f"""
            <div style="width:250px">

            <h4>Avião {callsign}</h4>

            <img src="{imagem_aviao}" width="220"><br><br>

            <b>Velocidade:</b> {velocidade}<br>
            <b>Latitude:</b> {lat}<br>
            <b>Longitude:</b> {lon}

            </div>
            """



            if lat is None or lon is None:
                continue

            folium.Marker(
            [lat, lon],
            popup=folium.Popup(texto, max_width=300),
            tooltip=f"Avião {callsign}",
            icon=folium.Icon(color="black", icon="plane", prefix="fa")
            ).add_to(mapa)

    except:
        print("Erro ao carregar aviões")

    mapa.save("mapa_aviao.html")


def atualizarAvioes():

    gerarMapaAvioes()

    caminho = os.path.abspath("mapa_aviao.html")
    browser.load(QUrl.fromLocalFile(caminho))



#LIMPAR CAMPOS DE ENDEREÇO

def limparCEP():
    CEP.clear()
    numero.clear()
    complemento.clear()
    lagradouro.clear()
    rua.clear()
    bairro.clear()
    cidade.clear()
    UF.setCurrentIndex(0)
    CEP.setFocus()


#salvar usuario
def salvarUsuario():
    with open("usuarios.json", "w") as arquivo:
     json.dump(usuarios, arquivo)


#carregar usuario
def carregarUsuarios():
    global usuarios
    if os.path.exists("usuarios.json"):
        with open("usuarios.json", "r") as arquivo:
            return json.load(arquivo)
    return {}
 
usuarios = carregarUsuarios()

print(usuarios)
print(usuarios["123.456.789-00"])  

#login ja existente

def validarJaCadastrado():
    CPF = caixaNomeJa.text()
    senha = caixaSenhaJa.text()
    

    if CPF == "" or senha == "":
        QMessageBox.critical(telaJaCadastrado, "ATENÇÃO", "Para validação os dois campos precisam ser informados. ")
        limparJa()

    elif CPF in usuarios and usuarios[CPF] == senha:
        QMessageBox.information(telaJaCadastrado, "Sucesso", f"Tenha um bom proveito!")
        telaJaCadastrado.hide()
        abrirTelaNavios()  
        limparJa()
        
    else:
        QMessageBox.critical(telaJaCadastrado, "Falha", "Dados de login incorretos!") 
        limparJa() 

  #limpar campos
def limparJa():
    caixaNomeJa.clear()
    caixaSenhaJa.clear()
    caixaNomeJa.setFocus()  
    

#validar campos do cadastro   

def validCampo():
    nome = caixaTextoNome.text() 
    dataDeNascimento = caixaTextoDataDeNascimento.text()
    CPF = caixaTextoCPF.text()
    endereco = caixaTextoEndereco.text()
    nomeDaMae = caixaTextoNomeDaMae.text()
    senha = caixaTextoSenha.text()

    if nome == "" or dataDeNascimento == "" or CPF == "" or endereco == "" or nomeDaMae == "" or senha == "":
        QMessageBox.critical(telalogin, "ATENÇÃO", "Todos os campos precisam ser informados.")
        return

# validar data
    try:
        dataConvertida = datetime.strptime(dataDeNascimento, "%d/%m/%Y")
    except ValueError:
        QMessageBox.critical(telalogin, "Erro", "Data inválida. Use DD/MM/AAAA.")
        return

    hoje = datetime.today()

# impedir data futura
    if dataConvertida > hoje:
        QMessageBox.critical(telalogin, "Erro", "A data não pode ser futura.")
        return

    # calcular idade
    idade = hoje.year - dataConvertida.year - (
        (hoje.month, hoje.day) < (dataConvertida.month, dataConvertida.day)
    )

    if idade < 18:
        QMessageBox.critical(telalogin, "Erro", "Usuário precisa ter pelo menos 18 anos.")
        return

    if CPF in usuarios:
        QMessageBox.critical(telalogin, "Erro", "Usuário já cadastrado!")
        return

    usuarios[CPF] = senha
    salvarUsuario()

    QMessageBox.information(telalogin, "Sucesso", "Cadastro realizado com sucesso!")

    limpaCampos()
    telalogin.hide()
    telaInicial.show()


#LIMPAR CAMPOS DO CADASTRO
    
def limpaCampos():
    caixaTextoNome.clear()
    caixaTextoDataDeNascimento.clear()
    caixaTextoCPF.clear()
    caixaTextoEndereco.clear()
    caixaTextoNomeDaMae.clear()
    caixaTextoCPF.setFocus()

#Criando a aplicação
app = QApplication(sys.argv)


with open ("estilo.qss", "r") as arquivo_qss:
    estilo = arquivo_qss.read()
    app.setStyleSheet(estilo)

#--------------tela inicial-------------
telaInicial = QWidget()
telaInicial.setWindowTitle("Tela Inicial")
telaInicial.setGeometry(100,100,300,200)

#Botões da tela inicial
botaoLogin = QPushButton('Cadastrar', telaInicial)
botaoLogin.move(100,50)

botaoCadastro = QPushButton('Entrar ', telaInicial)
botaoCadastro.move(100,100)
botaoLogin.clicked.connect(abrirLogin)
botaoCadastro.clicked.connect(abrirJaCadstrado)    



#--------------tela de ja cadastrado--------------
telaJaCadastrado = QWidget()
telaJaCadastrado.setWindowTitle("Já Cadastrado")
telaJaCadastrado.setGeometry(200,200,250,200)

QLabel("CPF:", telaJaCadastrado).move(50,30)
caixaNomeJa = QLineEdit(telaJaCadastrado)
caixaNomeJa.move(50,50)
caixaNomeJa.setInputMask("000.000.000-00")   

QLabel("Senha:", telaJaCadastrado).move(50,80)
caixaSenhaJa = QLineEdit(telaJaCadastrado)
caixaSenhaJa.setEchoMode(QLineEdit.Password)
caixaSenhaJa.move(50,100) 
caixaSenhaJa.setMaxLength(6)

botaoEntrarJa = QPushButton("Entrar", telaJaCadastrado)
botaoEntrarJa.move(70,140)
botaoEntrarJa.clicked.connect(validarJaCadastrado)

# ---------------- tela navios e avioes ----------------

telaNavio = QWidget()
telaNavio.setWindowTitle("Monitoramento Marítimo e Aviário em Tempo Real")
telaNavio.setGeometry(200,100,1200,800)

# Navegador que mostra o mapa
browser = QWebEngineView(telaNavio)
browser.setGeometry(20,20,1160,700)

botaoNavios = QPushButton("Buscar Navios", telaNavio)
botaoNavios.setGeometry(20,740,200,40)
botaoNavios.clicked.connect(atualizarMapaNavio)
threading.Thread(target=iniciar_websocket, daemon=True).start()

botaoAvioes = QPushButton("Buscar Aviões", telaNavio)
botaoAvioes.setGeometry(240,740,200,40)
botaoAvioes.clicked.connect(atualizarAvioes)



#---------------------tela de cadastro -------------------
telalogin = QWidget()
telalogin.setWindowTitle("Login")
telalogin.setGeometry(100,100,400,500)

labelMensagemLogin = QLabel("", telalogin)
labelMensagemLogin.setGeometry(100, 380, 300, 20)
labelMensagemLogin.setStyleSheet("color: red; font-weight: bold;")


#nome Label e caixa de texto
textoRotuloNome = QLabel('Nome completo:', telalogin)
textoRotuloNome.move(100 ,30)
regexNome = QRegExp("[a-zA-Z ]+")
validadorNome = QRegExpValidator(regexNome)
caixaTextoNome = QLineEdit(telalogin)
caixaTextoNome.setValidator(validadorNome)
caixaTextoNome.move(100,50)



# Data de nascimento label e caixa de texto
textoRotuloDataDeNascimento = QLabel('Data de Nascimento:', telalogin)
textoRotuloDataDeNascimento.move(100,80)

caixaTextoDataDeNascimento = QLineEdit(telalogin)       
caixaTextoDataDeNascimento.move(100,100)
caixaTextoDataDeNascimento.setInputMask("00/00/0000")



#CPF label e caixa de texto
textoRotuloCPF = QLabel('CPF:', telalogin)
textoRotuloCPF.move(100,130)
caixaTextoCPF = QLineEdit(telalogin)            
caixaTextoCPF.move(100,150)
caixaTextoCPF.setInputMask("000.000.000-00")   

#Endereco label e caixa de texto
textoRotuloEndereco = QLabel('Endereço:', telalogin)
textoRotuloEndereco.move(100,180)
caixaTextoEndereco = QLineEdit(telalogin)       
caixaTextoEndereco.move(100,200)
caixaTextoEndereco.setReadOnly(True)
caixaTextoEndereco.mousePressEvent = abrirEndereco


#Nome da mãe label e caixa de texto
textoRotuloNomeDaMae = QLabel('Nome da mãe:', telalogin)
textoRotuloNomeDaMae.move(100,230)

regexNomeMae = QRegExp("[a-zA-Z ]+")
validadorNomeMae = QRegExpValidator(regexNomeMae)
caixaTextoNomeDaMae = QLineEdit(telalogin)
caixaTextoNomeDaMae.setValidator(validadorNomeMae)
caixaTextoNomeDaMae.move(100,250)


# Senha label e caixa de texto
textoRotuloSenha = QLabel('Senha:', telalogin)
textoRotuloSenha.move(100,280)
caixaTextoSenha = QLineEdit(telalogin)
caixaTextoSenha.setEchoMode(QLineEdit.Password)
caixaTextoSenha.move(100,300)
caixaTextoSenha.setMaxLength(6)


#Criando botão
botao = QPushButton('Salvar', telalogin)
botao.move(70,400)
botao.clicked.connect(validCampo)

botaolimpar = QPushButton('Limpar', telalogin)
botaolimpar.move(145,400)
botaolimpar.clicked.connect(limpaCampos)

botaovoltar = QPushButton('Voltar', telalogin)
botaovoltar.move(219,400)   
botaovoltar.clicked.connect(lambda: (telalogin.hide(), telaInicial.show()))




#-------------tela endereço  label e caixa de texto---------
telaEndereco = QWidget()
telaEndereco.setWindowTitle("Cadastrar Endereço")
telaEndereco.setGeometry(200, 250, 350, 560)


# cep label e caixa de texto 
QLabel('CEP:', telaEndereco).move(80, 30)
CEP = QLineEdit(telaEndereco)
CEP.move(80, 50)
CEP.setFixedWidth(150)


# numero label e caixa de texto
QLabel('Número:', telaEndereco).move(80, 90)
numero = QLineEdit(telaEndereco)
numero.move(80, 110)
numero.setFixedWidth(150)

# complemento label e caixa de texto
QLabel('Complemento:', telaEndereco).move(80, 150)
complemento = QLineEdit(telaEndereco)
complemento.move(80, 170)
complemento.setFixedWidth(150)


# lagradouro label e caixa de texto
QLabel('Logradouro:', telaEndereco).move(80, 210)
lagradouro = QLineEdit(telaEndereco)
lagradouro.move(80, 230)
lagradouro.setFixedWidth(150)
lagradouro.setEnabled(False)


# rua label e caixa de texto 
QLabel('Rua:', telaEndereco).move(80, 270)
rua = QLineEdit(telaEndereco)
rua.move(80, 290)
rua.setFixedWidth(150)
rua.setEnabled(False)


# bairro label e caixa de texto 
QLabel('Bairro:', telaEndereco).move(80, 330)
bairro = QLineEdit(telaEndereco)
bairro.move(80, 350)
bairro.setFixedWidth(150)
bairro.setEnabled(False)


# cidade label e caixa de texto
QLabel('Cidade:', telaEndereco).move(80, 390)
cidade = QLineEdit(telaEndereco)
cidade.move(80, 410)
cidade.setFixedWidth(150)
cidade.setEnabled(False)


# uf label e caixa de texto
QLabel('UF:', telaEndereco).move(80, 450)
UF = QComboBox(telaEndereco)
UF.move(80, 470)
UF.setFixedWidth(150)
UF.setEnabled(False)

UF.addItems([
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA",
    "MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN",
    "RS","RO","RR","SC","SP","SE","TO"
])

#-----------Funcao Salvar endereço-----------

def salvarEndereco():
    CEP_texto = CEP.text()
    numero_texto = numero.text()
    complemento_texto = complemento.text()
    rua_texto = rua.text()
    bairro_texto = bairro.text()
    cidade_texto = cidade.text()
    UF_texto = UF.currentText()

    if CEP_texto == "" or numero_texto == "" or complemento_texto == "" or bairro_texto == "" or cidade_texto == "" or UF_texto == "":
        QMessageBox.critical(telaEndereco, "ATENÇÃO", "Para validação todos os campos precisam ser informados. ")

    else:
        enderecoCompleto = f"{CEP_texto}"
        caixaTextoEndereco.setText(enderecoCompleto)

        QMessageBox.information(telaEndereco, "Sucesso", f"Endereço cadastrado com sucesso!")
        telaEndereco.hide() 
        telalogin.show()

#validar CEP
def validarCEP():
    codigoCEP = CEP.text()
    if codigoCEP == "":
        QMessageBox.critical(telaEndereco, "Erro", "Por favor, insira um CEP.")
        CEP.setFocus()
        return
    else:
        tratarCEP(codigoCEP)


#tratar CEP        
def tratarCEP(codigoCEP):
    url = f"https://viacep.com.br/ws/{codigoCEP}/json/"
    try:
        resposta = requests.get(url)
        
        resposta.status_code == 200 and requests.get(url)
        dados = resposta.json()

        if "erro" in dados:
            QMessageBox.information(telaEndereco,"CEP não encontrado.", "red")
            limparCEP()
        else:
            lagradouro.setText(dados.get("logradouro", ""))
            bairro.setText(dados.get("bairro", ""))
            cidade.setText(dados.get("localidade", ""))
            UF.setCurrentText(dados.get("uf", ""))
    except Exception as e:
        QMessageBox.critical(telaEndereco, "Erro", f"Erro ao consultar o CEP: {e}")
        limparCEP()

botaoSalvarEndereco = QPushButton('Salvar Endereço', telaEndereco)
botaoSalvarEndereco.move(60, 520)   
botaoSalvarEndereco.clicked.connect(salvarEndereco) 

botaobuscarCEP = QPushButton('Buscar CEP', telaEndereco)
botaobuscarCEP.move(200, 520)
botaobuscarCEP.clicked.connect(validarCEP)


botao.clicked.connect(validCampo)

telaInicial.show()

sys.exit(app.exec_())

