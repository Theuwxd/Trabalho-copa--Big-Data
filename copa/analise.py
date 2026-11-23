import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))   #roda sempre a partir da pasta do script
os.makedirs("fig", exist_ok=True)                      #cria a pasta dos gráficos
import pandas as pd
import matplotlib
from scipy import stats

MOSTRAR_GRAFICO = True        
if not MOSTRAR_GRAFICO:
    matplotlib.use("Agg")      
import matplotlib.pyplot as plt

#lê a base que o 'etl.py' criou
base = pd.read_csv("dados/base_final.csv")

#deixa o grafico mais limpo
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})

#na tabela 1, ele pega o número de copas que cada país já jogou e compara com a populaçao.
#decidi utilizar a correlacao de spearman, onde o resultado vem como um número entre -1 e 1. 
#perto de 1, andam bem juntas, perto de 0, uma não tem nada a ver com a outra e perto de -1, uma sobe quando a outra desce
resultados = []
for coluna, nome in [("populacao", "População")]:
    dados = base.dropna(subset=[coluna])               #vai tirar os países que não têm esse dado
    rho, p = stats.spearmanr(dados[coluna], dados["participacoes"])
    resultados.append([nome, len(dados), round(rho, 2), round(p, 3)])

tab_corr = pd.DataFrame(resultados, columns=["Variável x Participações", "n", "rho", "p"])
tab_corr.to_csv("dados/tab_corr.csv", index=False)


#na tabela 2, mostra participaçao de acordo com o tamanho da populaçao
base["pop_milhoes"] = base["populacao"] / 1e6          #população em milhões
limites = [0, 5, 20, 60, 2000]                         #limites das faixas
nomes_faixas = ["Até 5 mi", "5 a 20 mi", "20 a 60 mi", "Mais de 60 mi"]
base["faixa"] = pd.cut(base["pop_milhoes"], bins=limites, labels=nomes_faixas)   #coloca cada país em uma faixa

grupo = base.groupby("faixa", observed=True)           #agrupa os países por faixa
tab_faixas = pd.DataFrame({
    "paises": grupo["cca3"].count(),                   #conta quantos países tem em cada faixa
    "ja_participou": grupo["ja_participou"].mean(),    #proporção que já jogou uma Copa
    "media": grupo["participacoes"].mean(),            #média de participações
})
tab_faixas.to_csv("dados/tab_faixas.csv")


#na tabela 3, é analisado os 10 países mais populosos
ordenado = base.sort_values("populacao", ascending=False)       #ordena do maior para o menor
tab_top = ordenado.head(10)[["pais", "populacao", "participacoes"]]
tab_top.to_csv("dados/tab_top.csv", index=False)

#mostrar as tabelas no terminal
print(tab_corr)
print(tab_faixas.round(2))
print(tab_top)


#grafico 1- relaçao entre populaçao e o numero de participaçoes em copas, onde cada bolinha vai representar um país
plt.figure(figsize=(6.5, 4))
plt.scatter(base["pop_milhoes"], base["participacoes"], color="#1f4e79", alpha=0.65, edgecolor="black")

#escreve o nome de alguns países no grafico, onde da pra adicionar mais ou mudar
destaques = ["India", "China", "Pakistan", "Brazil", "Germany", "Uruguay", "Nigeria", "Indonesia"]
for nome in destaques:
    linha = base[base["pais"] == nome].iloc[0]
    plt.annotate(nome, (linha["pop_milhoes"], linha["participacoes"]), xytext=(4, 4),
                 textcoords="offset points", fontsize=8)

plt.xscale("log")                                       #utilizei a escala log aq para deixar o grafico mais visual, pq se n fosse utilizado as bolinhas iriam ficar mto juntas
plt.xlabel("População em 2022 (milhões, na escala log)")
plt.ylabel("Participações em Copas (de 22)")
plt.tight_layout()
plt.savefig("fig/g1.png")                               #salva a imagem
if MOSTRAR_GRAFICO:
    plt.show()                                          #abre a janela
plt.close()


#grafico 2- media de participaçoes e % de países q ja participaram, separados por faixa populacional
figura, eixos = plt.subplots(1, 2, figsize=(6.5, 3))    #coloca dois gráficos lado a lado
eixos[0].bar(tab_faixas.index.astype(str), tab_faixas["media"], color="#2e8b57")
eixos[0].set_title("Participações (média)")
eixos[1].bar(tab_faixas.index.astype(str), tab_faixas["ja_participou"] * 100, color="#e07b00")
eixos[1].set_title("% que já disputou uma Copa")
for eixo in eixos:
    eixo.tick_params(axis="x", rotation=25)             #usei so pra inclinar os nomes das faixas
plt.tight_layout()
plt.savefig("fig/g2.png")
if MOSTRAR_GRAFICO:
    plt.show()
plt.close()