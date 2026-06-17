from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

@app.route('/')
def pagina_inicial():
    return "Servidor Render - Conexão Aberta Sefaz-CE! 🚀"

@app.route('/api/sefaz-ce', methods=['GET'])
def buscar_sefaz_ce():
    termo = request.args.get('busca', '').strip()
    cep = request.args.get('cep', '').strip().replace('-', '')
    
    if not termo or not cep:
        return jsonify({"erro": "CEP e Produto são obrigatórios"}), 400

    sessao = requests.Session()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'https://nfe.sefaz.ce.gov.br/'
    }
    
    url_busca = f"https://nfe.sefaz.ce.gov.br/pages/consultarNota.jsf?termo={requests.utils.quote(termo)}&cep={cep}"
    
    try:
        # Pega cookies iniciais
        sessao.get("https://nfe.sefaz.ce.gov.br/pages/consultarNota.jsf", headers=headers, timeout=10)
        # Faz a busca real com internet liberada pela Render
        resposta = sessao.get(url_busca, headers=headers, timeout=15)
        
        if resposta.status_code != 200:
            return jsonify({"erro": "A Sefaz rejeitou o acesso temporariamente."}), 502

        soup = BeautifulSoup(resposta.text, 'html.parser')
        resultados_reais = []

        # Puxa os blocos de notas fiscais geradas no site do governo
        tabela_produtos = soup.find_all('div', class_='painel-produto') or soup.find_all('tr', class_='linha-produto')

        for item in tabela_produtos:
            try:
                nome_prod = item.find(class_='nome-produto').text.strip().upper()
                preco_prod = item.find(class_='preco-produto').text.strip()
                mercado = item.find(class_='razao-social').text.strip().upper()
                
                end_tag = item.find(class_='endereco-posto')
                endereco_loja = end_tag.text.strip() if end_tag else "Endereço na Nota"
                
                hora_tag = item.find(class_='data-emissao')
                hora_nota = hora_tag.text.strip() if hora_tag else "Recente"

                preco_num = float(preco_prod.replace('R$', '').replace('.', '').replace(',', '.').strip())

                resultados_reais.append({
                    "produto": nome_prod,
                    "valor": preco_num,
                    "loja": mercado,
                    "endereco": endereco_loja,
                    "ultima_nota": f"📄 Nota emitida em: {hora_nota}"
                })
            except Exception:
                continue

        return jsonify(sorted(resultados_reais, key=lambda x: x['valor']))

    except Exception as e:
        return jsonify({"erro": "Falha ao conectar na Sefaz", "detalhes": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)