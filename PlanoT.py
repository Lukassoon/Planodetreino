import streamlit as st
import json
import os
import random
import string
from datetime import datetime
import pandas as pd

# Função para gerar uma senha temporária
def generate_temp_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# Função para carregar os dados dos treinadores
def load_trainers():
    if os.path.exists("trainers.json"):
        with open("trainers.json", "r") as f:
            return json.load(f)
    else:
        return {}

# Função para salvar os dados dos treinadores
def save_trainers(trainers):
    with open("trainers.json", "w") as f:
        json.dump(trainers, f)

# Função para carregar os dados dos alunos de um treinador
def load_trainer_students(trainer_login):
    filename = f"{trainer_login}_students.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
            # Garantir que o campo "last_id" exista
            if "last_id" not in data:
                data["last_id"] = 0
            if "students" not in data:
                data["students"] = {}
            
            # Garantir que todos os alunos tenham os campos necessários
            for student_id, student_info in data["students"].items():
                if "password" not in student_info:
                    student_info["password"] = None  # Inicializa a senha como None se não existir
                if "completed_workouts" not in student_info:
                    student_info["completed_workouts"] = 0  # Contador de treinos realizados
                if "weight_history" not in student_info:
                    student_info["weight_history"] = []  # Histórico de peso
                if "login" not in student_info:
                    # Gera um login padrão se não existir
                    student_info["login"] = f"{student_info['name'].split()[0].lower()}_{student_id}"
                if "email" not in student_info:
                    student_info["email"] = ""  # Inicializa o e-mail como vazio se não existir
                for workout in student_info.get("workouts", []):
                    if "completed" not in workout:
                        workout["completed"] = [False] * len(workout.get("exercises", []))
            
            return data
    else:
        # Se o arquivo não existir, criar uma estrutura inicial
        return {"last_id": 0, "students": {}}

# Função para salvar os dados dos alunos de um treinador
def save_trainer_students(trainer_login, data):
    filename = f"{trainer_login}_students.json"
    with open(filename, "w") as f:
        json.dump(data, f)

# Função para gerar um ID numérico sequencial
def generate_id(data):
    data["last_id"] += 1
    return f"{data['last_id']:03}"  # Formata o ID com 3 dígitos (001, 002, etc.)

# Interface do Treinador
def trainer_interface(trainer_login):
    st.title(f"🏋️‍♂️ Interface do Treinador: {trainer_login}")
    
    # Botão para sair
    if st.button("🚪 Sair"):
        st.session_state.trainer_logged_in = False
        st.session_state.trainer_login = None
        st.rerun()  # Recarrega a página para voltar à tela de login
    
    # Carregar os dados dos alunos do treinador
    data = load_trainer_students(trainer_login)
    
    # Adicionar novo aluno
    with st.expander("➕ Adicionar Novo Aluno", expanded=False):
        with st.form("add_student"):
            st.write("Preencha os dados do aluno:")
            col1, col2 = st.columns(2)
            with col1:
                student_name = st.text_input("Nome do Aluno")
            with col2:
                student_weight = st.number_input("Peso do Aluno (kg)", min_value=0.0)
            student_height = st.number_input("Altura do Aluno (cm)", min_value=0.0)
            student_email = st.text_input("E-mail do Aluno")
            submitted = st.form_submit_button("Adicionar Aluno")
            
            if submitted:
                student_id = generate_id(data)
                login = f"{student_name.split()[0].lower()}_{student_id}"  # Gera o login com o primeiro nome e ID
                data["students"][student_id] = {
                    "name": student_name,
                    "weight": student_weight,
                    "height": student_height,
                    "email": student_email,  # Adiciona o e-mail do aluno
                    "login": login,  # Adiciona o login gerado
                    "password": None,  # Senha inicialmente não definida
                    "completed_workouts": 0,  # Contador de treinos realizados
                    "weight_history": [{"weight": student_weight, "date": datetime.now().strftime("%Y-%m-%d")}],  # Inicializa o histórico de peso
                    "workouts": []
                }
                save_trainer_students(trainer_login, data)
                st.success(f"✅ Aluno adicionado com sucesso! ID do Aluno: {student_id}, Login: {login}")
                st.rerun()  # Recarrega a página para atualizar a lista de alunos

    # Lista de todos os alunos com busca integrada
    st.header("📋 Lista de Alunos")
    search_term = st.text_input("🔍 Buscar Aluno por ID ou Nome")
    
    # Adicionar a opção "Nenhum aluno" com ID 000
    filtered_students = [("000", {"name": "Nenhum aluno", "weight": 0, "height": 0})]
    for student_id, student_info in data["students"].items():
        if not search_term or search_term.lower() in student_id.lower() or search_term.lower() in student_info["name"].lower():
            filtered_students.append((student_id, student_info))
    
    if filtered_students:
        # Exibir lista de alunos filtrados
        selected_student = st.selectbox(
            "Selecione um aluno para ver detalhes",
            [f"{s[0]} - {s[1]['name']}" for s in filtered_students],
            key="student_list"
        )
        selected_student_id = selected_student.split(" - ")[0]
        
        # Verificar se o aluno selecionado não é "Nenhum aluno"
        if selected_student_id != "000":
            student = data["students"][selected_student_id]
            
            # Exibir informações do aluno selecionado
            st.header(f"👤 Aluno: {student['name']}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ID", selected_student_id)
            with col2:
                st.metric("Peso", f"{student['weight']} kg")
            with col3:
                st.metric("Altura", f"{student['height']} cm")
            
            # Exibir histórico de peso em uma tabela
            st.subheader("📊 Histórico de Peso")
            if student["weight_history"]:
                # Converter o histórico de peso em um DataFrame
                weight_history_df = pd.DataFrame(student["weight_history"])
                st.dataframe(weight_history_df)
            else:
                st.info("Nenhum dado de peso registrado.")
            
            # Aviso ao treinador se o aluno completou um número X de treinos
            if student["completed_workouts"] >= 5:  # Número X de treinos (ajuste conforme necessário)
                st.warning(f"⚠️ O aluno {student['name']} completou {student['completed_workouts']} treinos. Considere editar o treino.")
            
            # Botão para excluir o aluno
            if st.button(f"🗑️ Excluir Aluno {selected_student_id}"):
                del data["students"][selected_student_id]
                save_trainer_students(trainer_login, data)
                st.success(f"✅ Aluno {selected_student_id} excluído com sucesso!")
                st.rerun()  # Recarrega a página para atualizar a lista de alunos
            
            # Menu suspenso para editar informações do aluno
            with st.expander("✏️ Editar Informações do Aluno", expanded=False):
                with st.form("edit_student_info"):
                    new_name = st.text_input("Nome do Aluno", value=student["name"])
                    new_weight = st.number_input("Peso do Aluno (kg)", value=student["weight"])
                    new_height = st.number_input("Altura do Aluno (cm)", value=student["height"])
                    new_email = st.text_input("E-mail do Aluno", value=student["email"])
                    submitted = st.form_submit_button("Salvar Alterações")
                    
                    if submitted:
                        student["name"] = new_name
                        student["weight"] = new_weight
                        student["height"] = new_height
                        student["email"] = new_email
                        # Adiciona o novo peso ao histórico
                        student["weight_history"].append({"weight": new_weight, "date": datetime.now().strftime("%Y-%m-%d")})
                        save_trainer_students(trainer_login, data)
                        st.success("✅ Informações do aluno atualizadas com sucesso!")

            # Menu suspenso para adicionar treino
            with st.expander("➕ Adicionar Treino", expanded=False):
                with st.form("add_workout"):
                    workout_name = st.text_input("Nome do Treino", key=f"workout_name_{selected_student_id}")
                    workout_description = st.text_area("Descrição do Treino", key=f"workout_description_{selected_student_id}")
                    exercises = st.text_area("Exercícios (um por linha)", key=f"exercises_{selected_student_id}")
                    submitted = st.form_submit_button("Adicionar Treino")
                    
                    if submitted:
                        student["workouts"].append({
                            "name": workout_name,
                            "description": workout_description,
                            "exercises": exercises.split("\n"),
                            "completed": [False] * len(exercises.split("\n"))  # Inicializa as marcações como False
                        })
                        save_trainer_students(trainer_login, data)
                        st.success("✅ Treino adicionado com sucesso!")
                        st.rerun()  # Recarrega a página para limpar os campos

            # Exibir treinos do aluno
            st.header("📝 Treinos do Aluno")
            if not student["workouts"]:
                st.info("Nenhum treino disponível para este aluno.")
            else:
                for i, workout in enumerate(student["workouts"]):
                    with st.expander(f"🏋️‍♂️ Treino {i + 1}: {workout['name']}", expanded=False):
                        st.write(f"**Descrição:** {workout['description']}")
                        st.write("**Exercícios:**")
                        for j, exercise in enumerate(workout["exercises"]):
                            completed = st.checkbox(exercise, value=workout["completed"][j], key=f"{workout['name']}_{j}")
                            workout["completed"][j] = completed
                        
                        if st.button(f"✅ Finalizar Treino {i + 1}", key=f"finish_{i}"):
                            workout["completed"] = [False] * len(workout["exercises"])
                            student["completed_workouts"] += 1  # Incrementa o contador de treinos realizados
                            save_trainer_students(trainer_login, data)
                            st.success("✅ Treino finalizado! Marcações zeradas.")
                            st.rerun()  # Recarrega a página para atualizar as caixas de marcação
    else:
        st.info("Nenhum aluno encontrado com o termo de busca.")

# Interface do Aluno
def student_interface():
    st.title("👤 Interface do Aluno")
    
    # Carregar os dados dos alunos de todos os treinadores
    trainers = load_trainers()
    all_students = {}
    for trainer_login in trainers:
        data = load_trainer_students(trainer_login)
        all_students.update(data["students"])
    
    # Estado da sessão para controlar se o aluno já fez login
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "student_id" not in st.session_state:
        st.session_state.student_id = None
    if "trainer_login" not in st.session_state:
        st.session_state.trainer_login = None
    
    if not st.session_state.logged_in:
        # Campo para o aluno inserir o login
        student_login = st.text_input("🔑 Digite seu login para acessar seus treinos", value=st.session_state.get("saved_student_login", ""))
        
        # Caixa de seleção "Lembrar do Login"
        remember_login = st.checkbox("Lembrar do Login", value=st.session_state.get("remember_student_login", False))
        
        # Botão para acessar treinos
        if st.button("🚀 Acessar Treinos"):
            # Encontrar o aluno pelo login
            student = None
            for trainer_login in trainers:
                data = load_trainer_students(trainer_login)
                for student_id, student_info in data["students"].items():
                    if student_info.get("login") == student_login:  # Verifica o login
                        student = student_info
                        st.session_state.student_id = student_id
                        st.session_state.trainer_login = trainer_login  # Salva o login do treinador
                        break
                if student:
                    break
            
            if student:
                # Salvar o login se a caixa "Lembrar do Login" estiver marcada
                if remember_login:
                    st.session_state.saved_student_login = student_login
                    st.session_state.remember_student_login = True
                else:
                    st.session_state.saved_student_login = ""
                    st.session_state.remember_student_login = False
                
                # Verificar se é o primeiro acesso (senha ainda não definida)
                if student["password"] is None:
                    st.session_state.first_access = True
                    st.rerun()  # Recarrega a página para mostrar o formulário de definição de senha
                else:
                    st.session_state.first_access = False
                    st.rerun()  # Recarrega a página para mostrar o campo de senha
            else:
                st.error("❌ Login do Aluno não encontrado.")
        
        # Botão para recuperar senha (menor e abaixo do botão "Acessar Treinos")
        if st.button("🔓 Esqueci minha senha", key="forgot_password_button"):
            with st.form("forgot_password_form"):
                st.write("🔐 Recuperação de Senha")
                recovery_email = st.text_input("Digite seu e-mail para recuperar a senha")
                submitted = st.form_submit_button("Recuperar Senha")
                
                if submitted:
                    student = None
                    for trainer_login in trainers:
                        data = load_trainer_students(trainer_login)
                        for student_id, student_info in data["students"].items():
                            if student_info.get("email") == recovery_email:  # Verifica o e-mail
                                student = student_info
                                break
                        if student:
                            break
                    
                    if student:
                        # Gerar uma nova senha temporária
                        temp_password = generate_temp_password()
                        student["password"] = temp_password
                        
                        # Salvar a nova senha
                        save_trainer_students(trainer_login, data)
                        st.success(f"✅ Um e-mail foi enviado para {recovery_email} com a nova senha temporária: **{temp_password}**")
                        st.info("🔑 Use esta senha para fazer login e altere-a após o acesso.")
                    else:
                        st.error("❌ E-mail do Aluno não encontrado.")
        
        # Se for o primeiro acesso, mostrar formulário para definir senha
        if "first_access" in st.session_state and st.session_state.first_access:
            with st.form("first_access_form"):
                st.write("🔐 Primeiro acesso: Defina sua senha")
                new_password = st.text_input("Digite sua senha", type="password")
                confirm_password = st.text_input("Confirme sua senha", type="password")
                submitted = st.form_submit_button("Salvar Senha")
                
                if submitted:
                    if new_password == confirm_password:
                        # Salvar a senha no perfil do aluno
                        data = load_trainer_students(st.session_state.trainer_login)
                        data["students"][st.session_state.student_id]["password"] = new_password
                        save_trainer_students(st.session_state.trainer_login, data)
                        st.session_state.logged_in = True
                        st.session_state.first_access = False
                        st.rerun()  # Recarrega a página para esconder o formulário de senha
                    else:
                        st.error("❌ As senhas não coincidem. Tente novamente.")
        
        # Se não for o primeiro acesso, mostrar campo de senha
        elif "first_access" in st.session_state and not st.session_state.first_access:
            password = st.text_input("🔑 Digite sua senha", type="password")
            
            if st.button("🔓 Confirmar Senha"):
                data = load_trainer_students(st.session_state.trainer_login)
                student = data["students"][st.session_state.student_id]
                if password == student["password"]:
                    st.session_state.logged_in = True
                    st.rerun()  # Recarrega a página para esconder a caixa de login
                else:
                    st.error("❌ Senha incorreta. Tente novamente.")
    else:
        # Aluno já fez login, exibir treinos
        data = load_trainer_students(st.session_state.trainer_login)
        student = data["students"][st.session_state.student_id]
        
        st.header(f"👤 Aluno: {student['name']}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Peso", f"{student['weight']} kg")
        with col2:
            st.metric("Altura", f"{student['height']} cm")
        with col3:
            st.metric("Treinos Realizados", student["completed_workouts"])
        
        # Exibir histórico de peso em uma tabela
        st.subheader("📊 Histórico de Peso")
        if student["weight_history"]:
            weight_history_df = pd.DataFrame(student["weight_history"])
            st.dataframe(weight_history_df)
        else:
            st.info("Nenhum dado de peso registrado.")
        
        # Botão para sair
        if st.button("🚪 Sair"):
            st.session_state.logged_in = False
            st.session_state.student_id = None
            st.session_state.trainer_login = None
            st.rerun()  # Recarrega a página para voltar à tela de login
        
        # Exibir treinos do aluno
        st.header("📝 Treinos do Aluno")
        if not student["workouts"]:
            st.info("Nenhum treino disponível no momento.")
        else:
            for workout in student["workouts"]:
                with st.expander(f"🏋️‍♂️ Treino: {workout['name']}", expanded=False):
                    st.write(f"**Descrição:** {workout['description']}")
                    st.write("**Exercícios:**")
                    for i, exercise in enumerate(workout["exercises"]):
                        completed = st.checkbox(exercise, value=workout["completed"][i], key=f"{workout['name']}_{i}")
                        workout["completed"][i] = completed
                    
                    if st.button(f"✅ Finalizar Treino: {workout['name']}", key=f"finish_{workout['name']}"):
                        workout["completed"] = [False] * len(workout["exercises"])
                        student["completed_workouts"] += 1  # Incrementa o contador de treinos realizados
                        save_trainer_students(st.session_state.trainer_login, data)
                        st.success("✅ Treino finalizado! Marcações zeradas.")
                        st.rerun()  # Recarrega a página para atualizar as caixas de marcação

# Interface de Início
def home_interface():
    # Verificar se o treinador ou o aluno já está logado
    if "trainer_logged_in" not in st.session_state:
        st.session_state.trainer_logged_in = False
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    # Se o treinador ou o aluno estiver logado, redirecionar para a interface correta
    if st.session_state.trainer_logged_in:
        trainer_interface(st.session_state.trainer_login)
    elif st.session_state.logged_in:
        student_interface()
    else:
        # Layout da tela inicial
        st.title("🏋️‍♂️ Bem-vindo ao App de Treinos")
        st.write("Escolha sua opção abaixo:")
        
        # Usar colunas para organizar os botões
        col1, col2 = st.columns(2)
        
        with col1:
            st.header("👨‍🏫 Treinador")
            st.write("Gerencie seus alunos e treinos.")
            if st.button("Acessar como Treinador"):
                st.session_state.user_type = "Treinador"
                st.rerun()
        
        with col2:
            st.header("👤 Aluno")
            st.write("Acesse seus treinos e acompanhe seu progresso.")
            if st.button("Acessar como Aluno"):
                st.session_state.user_type = "Aluno"
                st.rerun()
        
        # Se o usuário escolheu uma opção, exibir o formulário correspondente
        if "user_type" in st.session_state:
            if st.session_state.user_type == "Treinador":
                # Opção para registrar ou fazer login
                option = st.radio("Escolha uma opção", ["Registrar", "Login"])
                
                if option == "Registrar":
                    with st.form("trainer_register_form"):
                        st.write("📝 Registro de Treinador")
                        email = st.text_input("E-mail")
                        login = st.text_input("Login")
                        password = st.text_input("Senha", type="password")
                        confirm_password = st.text_input("Confirme sua senha", type="password")
                        submitted = st.form_submit_button("Registrar")
                        
                        if submitted:
                            if password == confirm_password:
                                trainers = load_trainers()
                                if login in trainers:
                                    st.error("❌ Login já existe. Escolha outro login.")
                                else:
                                    trainers[login] = {
                                        "email": email,
                                        "password": password
                                    }
                                    save_trainers(trainers)
                                    st.success("✅ Treinador registrado com sucesso!")
                            else:
                                st.error("❌ As senhas não coincidem. Tente novamente.")
                
                elif option == "Login":
                    with st.form("trainer_login_form"):
                        st.write("🔑 Login do Treinador")
                        login = st.text_input("Login", value=st.session_state.get("saved_trainer_login", ""))
                        remember_login = st.checkbox("Lembrar do Login", value=st.session_state.get("remember_trainer_login", False))
                        password = st.text_input("Senha", type="password")
                        submitted = st.form_submit_button("Login")
                        
                        if submitted:
                            trainers = load_trainers()
                            if login in trainers and trainers[login]["password"] == password:
                                # Salvar o login se a caixa "Lembrar do Login" estiver marcada
                                if remember_login:
                                    st.session_state.saved_trainer_login = login
                                    st.session_state.remember_trainer_login = True
                                else:
                                    st.session_state.saved_trainer_login = ""
                                    st.session_state.remember_trainer_login = False
                                
                                st.session_state.trainer_logged_in = True
                                st.session_state.trainer_login = login
                                st.rerun()  # Recarrega a página para mostrar a interface do treinador
                            else:
                                st.error("❌ Login ou senha incorretos.")
            
            elif st.session_state.user_type == "Aluno":
                # Direcionar para a interface do aluno
                student_interface()

# Menu principal
def main():
    home_interface()

if __name__ == "__main__":
    main()