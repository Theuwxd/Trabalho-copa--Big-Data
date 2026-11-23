import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))   #roda sempre a partir da pasta do script
os.makedirs("dados", exist_ok=True)                    #cria a pasta dos dados
os.makedirs("fig", exist_ok=True)                      #cria a pasta dos gráficos
import json
import sqlite3
import urllib.request
import pandas as pd

SITE = "https://raw.githubusercontent.com"            #início dos endereços de download

ANO = 2022

#utiliza a primeira fonte: base relacional, com os historicos das partidas das copas
#aq é baixada a tabela de partidas onde cada linha é um jogo, com dois times q ja jogaram
tabela = pd.read_csv(SITE + "/jfjelstul/worldcup/master/data-csv/matches.csv")

#guarda a tabela em um banco SQLite
con = sqlite3.connect("dados/copa.sqlite")
tabela.to_sql("partidas", con, if_exists="replace", index=False)

#aq consulta o sql, onde pega a ediçao da copa e o time q jogou em casa(mandante) de cada partida 
mandantes = pd.read_sql_query(
    "SELECT tournament_id, home_team_code AS codigo FROM partidas WHERE tournament_name NOT LIKE '%Women%'", con)

#aq ele faz a msm coisa, porem pega o time q jogou fora(visitante) de cada partida 
visitantes = pd.read_sql_query(
    "SELECT tournament_id, away_team_code AS codigo FROM partidas WHERE tournament_name NOT LIKE '%Women%'", con)
con.close()

#aq e juntado as duas listas em uma so(mandante e visitante)
todos = pd.concat([mandantes, visitantes])
todos = todos.drop_duplicates()     #aq é tirada as linhas repitidas, para q cada time seja contado uma vez so em cada copa 
copa = todos.groupby("codigo").size().reset_index(name="participacoes")    #aq e contada quantas ediçoes cada time participou 


#aq é utilizada a segunda fonte: os documentos JSON no modelo NoSQL, com um documento pra cada país
resposta = urllib.request.urlopen(SITE + "/mledoze/countries/master/countries.json")
documentos = json.load(resposta)

lista = []
for d in documentos:
    if d.get("independent"):                           #pega so países idependentes 
        lista.append({"cca3": d["cca3"],               #pega o código do país sendo utilizado como uma chave pra ligar as 3 fontes 
                      "pais": d["name"]["common"],     #aq o nome fica guardado dentro de 'name'
                      "regiao": d.get("region")})
paises = pd.DataFrame(lista)


#aq é utilizada a terceira fonte escolhida sendo: planilha excel do banco mundial, onde contem a populaçao de cada país
pop_csv = pd.read_csv(SITE + "/datasets/population/main/data/population.csv")

#aq é montada uma planilha excel com uma aba(populaçao) e depois lê de volta
with pd.ExcelWriter("dados/banco_mundial.xlsx") as planilha:
    pop_csv.to_excel(planilha, sheet_name="Populacao", index=False)
pop = pd.read_excel("dados/banco_mundial.xlsx", sheet_name="Populacao")


#aq irá arruma os dados e juntar as 3 fontes
#tira as seleções que não existem como país no banco mundial
copa = copa[~copa["codigo"].isin(["DDR", "SCO", "WAL", "NIR"])]

#troca códigos antigos pelo país de hoje 
#ex:URSS vira rússia
copa["cca3"] = copa["codigo"].replace({"CSK": "CZE", "SCG": "SRB", "YUG": "SRB", "SUN": "RUS", "ENG": "GBR"})

#vai somar as participações de códigos que viraram o mesmo país
copa = copa.drop(columns="codigo")
copa = copa.groupby("cca3", as_index=False).sum()

#no excel vai ficar so o ano escolhido e renomeia as colunas
pop = pop[pop["Year"] == ANO]
pop = pop.rename(columns={"Country Code": "cca3", "Value": "populacao"})[["cca3", "populacao"]]

#aq vai juntar tudo, começando pela lista de todos os países
base = paises.merge(copa, on="cca3", how="left")
base = base.merge(pop, on="cca3", how="left")


#os países q nao tem participaçoes na copa vira 0 participações
base["participacoes"] = base["participacoes"].fillna(0).astype(int)

#tira os países sem populaçao e cria as colunas novas
base = base.dropna(subset=["populacao"])
base.loc[base["cca3"] == "GBR", "pais"] = "England (dados do Reino Unido)"
base["ja_participou"] = base["participacoes"] > 0

#aq salva a base final em CSV
base.to_csv("dados/base_final.csv", index=False)
#é mostrado um resumo de tudo no terminal
print(f"Base final: {len(base)} países | já participaram: {base.ja_participou.sum()} | nunca: {(~base.ja_participou).sum()}")