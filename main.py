import random
import uuid
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

fake = Faker("pt_BR")

NUM_USUARIOS = 200
NUM_EVENTOS = 40
NUM_APOSTAS = 5000
    
PORCENTAGEM_FRAUDADORES = 0.08

usuarios = []

fraudadores_ids = set()

for i in range(NUM_USUARIOS):

    user_id = str(uuid.uuid4())[:8]

    usuario = {
        "user_id": user_id,
        "nome": fake.name(),
        "ip": fake.ipv4_public(),
        "fraudador": False
    }

    usuarios.append(usuario)

qtd_fraudadores = int(NUM_USUARIOS * PORCENTAGEM_FRAUDADORES)

fraudadores_escolhidos = random.sample(usuarios, qtd_fraudadores)

for u in fraudadores_escolhidos:
    u["fraudador"] = True
    fraudadores_ids.add(u["user_id"])

usuarios_df = pd.DataFrame(usuarios)

eventos = []

base_time = datetime.now()

for i in range(NUM_EVENTOS):

    evento_id = str(uuid.uuid4())[:8]

    evento_time = base_time + timedelta(minutes=i * 15)

    evento = {
        "evento_id": evento_id,
        "jogo": f"Time_{random.randint(1,20)} vs Time_{random.randint(21,40)}",
        "timestamp_evento": evento_time,
        "odd_mercado": round(random.uniform(1.2, 3.5), 2)
    }

    eventos.append(evento)

eventos_df = pd.DataFrame(eventos)

apostas = []

for i in range(NUM_APOSTAS):

    usuario = random.choice(usuarios)
    evento = random.choice(eventos)

    odd_real = evento["odd_mercado"]

    fraudador = usuario["fraudador"]

    if not fraudador:

        odd_pega = round(
            random.uniform(
                odd_real * 0.95,
                odd_real * 1.05
            ),
            2
        )

        delay_ms = random.randint(500, 8000)

        chance_vitoria = 1 / odd_real

    else:

        exploit = random.random()

        if exploit < 0.7:

            odd_pega = round(
                odd_real * random.uniform(1.8, 3.5),
                2
            )

            delay_ms = random.randint(0, 400)

            chance_vitoria = 0.82

        else:

            odd_pega = round(
                odd_real * random.uniform(4, 8),
                2
            )

            delay_ms = random.randint(0, 150)

            chance_vitoria = 0.93

    venceu = random.random() < chance_vitoria

    valor = random.randint(50, 2000)

    lucro = (valor * odd_pega - valor) if venceu else -valor

    aposta = {
        "bet_id": str(uuid.uuid4())[:8],
        "user_id": usuario["user_id"],
        "evento_id": evento["evento_id"],
        "fraudador_real": fraudador,
        "odd_real": odd_real,
        "odd_pega": odd_pega,
        "delay_ms": delay_ms,
        "valor": valor,
        "venceu": venceu,
        "lucro": round(lucro, 2),
    }

    apostas.append(aposta)

apostas_df = pd.DataFrame(apostas)

apostas_df["odd_ratio"] = (
    apostas_df["odd_pega"] / apostas_df["odd_real"]
)

estatisticas = []

for user_id, grupo in apostas_df.groupby("user_id"):

    total_apostas = len(grupo)

    winrate = grupo["venceu"].mean()

    roi = grupo["lucro"].sum() / grupo["valor"].sum()

    media_delay = grupo["delay_ms"].mean()

    odd_ratio_media = grupo["odd_ratio"].mean()

    score = 0

    motivos = []

    if media_delay < 600:
        score += 30
        motivos.append("latência extremamente baixa")


    if odd_ratio_media > 1.7:
        score += 35
        motivos.append("captura de odds inconsistentes")

    if winrate > 0.75:
        score += 20
        motivos.append("taxa de vitória anormal")

    if roi > 1.5:
        score += 25
        motivos.append("ROI estatisticamente improvável")

    suspeito = score >= 60

    estatisticas.append({
        "user_id": user_id,
        "total_apostas": total_apostas,
        "winrate": round(winrate, 2),
        "roi": round(roi, 2),
        "media_delay_ms": round(media_delay, 2),
        "odd_ratio_media": round(odd_ratio_media, 2),
        "score_risco": score,
        "suspeito": suspeito,
        "motivos": motivos,
        "fraudador_real": user_id in fraudadores_ids
    })

estatisticas_df = pd.DataFrame(estatisticas)

alertas = estatisticas_df[
    estatisticas_df["suspeito"] == True
]

print("RESUMO DA SIMULAÇÃO")

print(f"Usuários: {NUM_USUARIOS}")
print(f"Eventos: {NUM_EVENTOS}")
print(f"Apostas: {NUM_APOSTAS}")

print("\nFraudadores reais:")
print(len(fraudadores_ids))

print("\nUsuários detectados:")
print(len(alertas))


verdadeiros_positivos = len(
    alertas[alertas["fraudador_real"] == True]
)

falsos_positivos = len(
    alertas[alertas["fraudador_real"] == False]
)

print("MÉTRICAS")
print(f"Verdadeiros positivos: {verdadeiros_positivos}")
print(f"Falsos positivos: {falsos_positivos}")

print("ALERTAS GERADOS")

for _, row in alertas.head(15).iterrows():

    print(f"""
USUÁRIO: {row['user_id']}
SCORE: {row['score_risco']}
WINRATE: {row['winrate']}
ROI: {row['roi']}
DELAY MÉDIO: {row['media_delay_ms']} ms
ODD RATIO: {row['odd_ratio_media']}
MOTIVOS: {", ".join(row['motivos'])}
FRAUDADOR REAL: {row['fraudador_real']}
""")

usuarios_df.to_csv("usuarios.csv", index=False)
eventos_df.to_csv("eventos.csv", index=False)
apostas_df.to_csv("apostas.csv", index=False)
estatisticas_df.to_csv("analise_risco.csv", index=False)

print("\nArquivos CSV exportados.")