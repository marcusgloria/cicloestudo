import streamlit as st  
import pandas as pd  
from datetime import datetime, timedelta  
import json  
import base64  
import io  

class CicloEstudos:  
    def __init__(self):  
        if 'disciplinas' not in st.session_state:  
            st.session_state.disciplinas = {}  
        if 'tempo_disponivel' not in st.session_state:  
            st.session_state.tempo_disponivel = 0  
        self.dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']  

    def calcular_prioridade(self, peso, nivel):  
        nivel_valor = {'A': 1, 'B': 2, 'C': 3}  
        return peso * nivel_valor[nivel]  

    def gerar_cronograma(self):  
        if not st.session_state.disciplinas or not st.session_state.tempo_disponivel:  
            st.warning("Por favor, adicione disciplinas e defina o tempo disponível primeiro.")  
            return None  

        total_prioridade = sum(disc['prioridade'] for disc in st.session_state.disciplinas.values())  
        cronograma = []  

        for dia in self.dias_semana[:-1]:  # Excluindo domingo  
            dia_cronograma = {'Dia': dia, 'Atividades': []}  
            tempo_restante = st.session_state.tempo_disponivel * 60  # Convertendo para minutos  

            for disc, info in st.session_state.disciplinas.items():  
                tempo_disciplina = (info['prioridade'] / total_prioridade) * tempo_restante  
                if tempo_disciplina >= 30:  
                    dia_cronograma['Atividades'].append({  
                        'Disciplina': disc,  
                        'Tempo': round(tempo_disciplina),  
                        'Tipo': 'Estudo'  
                    })  

            tempo_revisao = tempo_restante * 0.2  
            tempo_exercicios = tempo_restante * 0.2  

            dia_cronograma['Atividades'].append({  
                'Disciplina': 'Revisão',  
                'Tempo': round(tempo_revisao),  
                'Tipo': 'Revisão'  
            })  

            dia_cronograma['Atividades'].append({  
                'Disciplina': 'Exercícios',  
                'Tempo': round(tempo_exercicios),  
                'Tipo': 'Exercícios'  
            })  

            cronograma.append(dia_cronograma)  

        sabado = {  
            'Dia': 'Sábado',  
            'Atividades': [  
                {'Disciplina': 'Revisão Geral', 'Tempo': round(st.session_state.tempo_disponivel * 30), 'Tipo': 'Revisão'},  
                {'Disciplina': 'Simulado', 'Tempo': round(st.session_state.tempo_disponivel * 30), 'Tipo': 'Simulado'}  
            ]  
        }  
        cronograma.append(sabado)  

        return cronograma  

def get_download_link(df, filename, text):  
    towrite = io.BytesIO()  
    df.to_excel(towrite, index=False, engine='openpyxl')  
    towrite.seek(0)  
    b64 = base64.b64encode(towrite.read()).decode()  
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">{text}</a>'  

def main():  
    st.set_page_config(page_title="Organizador de Estudos para Concursos", layout="wide")  

    st.title("📚 Organizador de Ciclo de Estudos para Concursos")  

    ciclo = CicloEstudos()  

    # Sidebar para adicionar disciplinas  
    with st.sidebar:  
        st.header("Adicionar Disciplina")  
        with st.form("adicionar_disciplina"):  
            nome = st.text_input("Nome da disciplina")  
            peso = st.slider("Peso da disciplina no edital", 1, 10, 5)  
            nivel = st.selectbox("Seu nível de conhecimento",   
                               options=['A', 'B', 'C'],  
                               format_func=lambda x: {'A': 'Bom', 'B': 'Médio', 'C': 'Iniciante'}[x])  

            submitted = st.form_submit_button("Adicionar Disciplina")  

            if submitted and nome:  
                st.session_state.disciplinas[nome] = {  
                    'peso': peso,  
                    'nivel': nivel,  
                    'prioridade': ciclo.calcular_prioridade(peso, nivel)  
                }  
                st.success(f"Disciplina '{nome}' adicionada com sucesso!")  

        # Tempo disponível  
        st.header("Tempo Disponível")  
        tempo = st.number_input("Horas por dia disponíveis para estudo",   
                              min_value=1.0, max_value=24.0, value=4.0, step=0.5)  
        if st.button("Definir Tempo"):  
            st.session_state.tempo_disponivel = tempo  
            st.success(f"Tempo definido: {tempo} horas por dia")  

    # Main area  
    col1, col2 = st.columns([2, 1])  

    with col1:  
        st.header("Disciplinas Cadastradas")  
        if st.session_state.disciplinas:  
            df_disciplinas = pd.DataFrame.from_dict(st.session_state.disciplinas, orient='index')  
            df_disciplinas['nivel'] = df_disciplinas['nivel'].map({'A': 'Bom', 'B': 'Médio', 'C': 'Iniciante'})  
            st.dataframe(df_disciplinas)  

            if st.button("Limpar todas as disciplinas"):  
                st.session_state.disciplinas = {}  
                st.experimental_rerun()  
        else:  
            st.info("Nenhuma disciplina cadastrada ainda.")  

    with col2:  
        st.header("Tempo Definido")  
        if st.session_state.tempo_disponivel:  
            st.info(f"{st.session_state.tempo_disponivel} horas por dia")  
        else:  
            st.info("Tempo não definido")  

    # Gerar Cronograma  
    if st.button("Gerar Cronograma"):  
        cronograma = ciclo.gerar_cronograma()  

        if cronograma:  
            st.header("Cronograma Semanal")  

            # Criar DataFrame para exibição  
            df_list = []  
            for dia in cronograma:  
                for atividade in dia['Atividades']:  
                    df_list.append({  
                        'Dia': dia['Dia'],  
                        'Disciplina': atividade['Disciplina'],  
                        'Tempo (horas)': round(atividade['Tempo'] / 60, 2),  
                        'Tipo': atividade['Tipo']  
                    })  

            df = pd.DataFrame(df_list)  

            # Exibir cronograma  
            st.dataframe(df)  

            # Download buttons  
            st.markdown("### Downloads")  
            col1, col2 = st.columns(2)  

            with col1:  
                st.markdown(get_download_link(df, "cronograma_semanal.xlsx",   
                                           "📥 Baixar Cronograma (Excel)"), unsafe_allow_html=True)  

            with col2:  
                json_str = json.dumps(cronograma, ensure_ascii=False, indent=2)  
                b64 = base64.b64encode(json_str.encode()).decode()  
                href = f'<a href="data:application/json;base64,{b64}" download="cronograma_semanal.json">📥 Baixar Cronograma (JSON)</a>'  
                st.markdown(href, unsafe_allow_html=True)  

            # Visualização por dia  
            st.header("Visualização Detalhada por Dia")  
            dia_selecionado = st.selectbox("Selecione o dia", options=[dia['Dia'] for dia in cronograma])  

            df_dia = df[df['Dia'] == dia_selecionado]  

            # Gráfico de pizza para distribuição do tempo  
            import plotly.express as px  
            fig = px.pie(df_dia, values='Tempo (horas)', names='Disciplina',   
                        title=f'Distribuição do Tempo - {dia_selecionado}')  
            st.plotly_chart(fig)  

if __name__ == "__main__":  
    main()  
