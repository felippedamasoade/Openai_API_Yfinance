import openai
import yfinance as yf
import dotenv
from dotenv import load_dotenv
import os
import json
import pandas as pd

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def retorna_cotacao_acao_historica(ticker, periodo='1mo'):
    
    
    ticker = ticker.replace('.SA','')
    print('retorna_cotacao_acao_historica', ticker)
    # Obtendo as cotações de ações
    ticker_obj = yf.Ticker(f'{ticker}.SA')
    # Pegando as ações daquele período
    hist = ticker_obj.history(period=periodo)
    # Transformando o datetime em string
    hist.index = hist.index.strftime('%m-%d-%Y')
    # Botando o arquivo em JSON
    hist = round(hist, 2)
    # Ajustando o tamanho do DataFrame hist para reduzir o número de registros a 30
    if len(hist) > 30:
        slice_size = int(len(hist) / 30)
        hist = hist.iloc[::-slice_size][::-1]
    return hist.to_json()

tools = [
    {
        'type': 'function',
        'function': {
            'name': 'retorna_cotacao_acao_historica',
            'description': 'Retorna a cotação diária histórica para uma ação da Bovespa',
            'parameters': {
                'type': 'object',
                'properties': {
                    'ticker': {
                        'type': 'string',
                        'description': 'O Ticker da ação. Exemplo: "ABEV3" para Ambev, para Petrobras etc.'
                    },
                    'periodo': {
                        'type': 'string',
                        'description': 'O período que será retornado de dados históricos '
                                       'sendo "1mo" equivalente a um mês de dados, "1d" '
                                       'a 1 dia e "1y" a 1 ano',
                        'enum': ["1d", "5d", "1mo", "6mo", "1y", "5y", "10y", "ytd", "max"]
                    }
                }
            }
        }
    }
]

funcoes_disponiveis = {'retorna_cotacao_acao_historica': retorna_cotacao_acao_historica}

def geracao_texto(mensagens):
    response = openai.chat.completions.create(
        messages=mensagens,
        model="gpt-3.5-turbo",
        tools=tools,
        tool_choice='auto'
    )

    tool_calls = response.choices[0].message.tool_calls

    if tool_calls:
        mensagens.append(response.choices[0].message)
        for tool_call in tool_calls:
            func_name = tool_call.function.name
            function_to_call = funcoes_disponiveis[func_name]
            func_args = json.loads(tool_call.function.arguments)
            func_retrun = function_to_call(**func_args)
            mensagens.append({
                'tool_call_id': tool_call.id,
                'role': 'tool',
                'name': func_name,
                'content': func_retrun
            })

    segunda_resposta = openai.chat.completions.create(
        messages=mensagens,
        model="gpt-3.5-turbo"
    )

    mensagens.append(segunda_resposta.choices[0].message)
    print(f'Assistant: {mensagens[-1].content}')
    return mensagens


if __name__ == '__main__':

    print('Bem-vindo ao ChatBot Finance ')
    
    while True:
        input_usuario = input('User: ')

        mensagens = [{'role':'user','content':input_usuario}]
        mensagens = geracao_texto(mensagens)