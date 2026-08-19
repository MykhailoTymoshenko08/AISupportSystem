import streamlit as st
import requests
import os

API_URL = os.environ.get("API_URL", "http://localhost:8000/api/v1")

st.set_page_config(page_title="Nebula Support Hub", page_icon="🌌", layout="wide")

st.sidebar.title("Nebula AI Tools")
app_mode = st.sidebar.radio("Оберіть інструмент:", ["AI Router (Task 1)", "Agent Copilot (Task 2)"])

if app_mode == "AI Router (Task 1)":
    st.title("AI Ticket Classifier")
    st.markdown("Автоматична маршрутизація звернень. Введіть текст тікету, і ШІ визначить категорію, пріоритет та наступний крок.")

    sample_tickets = {
        "1. Базовий (Billing)": "Hi, I want to upgrade from monthly to yearly subscription.",
        "2. Агресія (Edge Case)": "WHY IS MY APP NOT WORKING??? YOU IDIOTS TOOK MY MONEY AND THE SCREEN IS BLANK!!!",
        "3. Юридична погроза (Human-in-loop)": "You charged me twice. If you don't refund me today, I will contact my lawyer and the authorities.",
        "4. Змішана мова (Edge Case)": "Hello, у мене проблема з payment — гроші списались двічі, please refund."
    }
    
    selected_sample = st.selectbox("Оберіть шаблон для швидкого тесту (або напишіть свій):", ["(Свій текст)"] + list(sample_tickets.keys()))
    
    default_text = ""
    if selected_sample != "(Свій текст)":
        default_text = sample_tickets[selected_sample]

    ticket_text = st.text_area("Текст звернення (Ticket Text):", value=default_text, height=150)

    if st.button("Класифікувати тікет", type="primary"):
        if not ticket_text.strip():
            st.warning("Будь ласка, введіть текст тікету.")
        else:
            with st.spinner("Аналізую звернення..."):
                try:
                    response = requests.post(
                        f"{API_URL}/tickets/classify", 
                        json={"text": ticket_text}
                    )
                    response.raise_for_status()
                    data = response.json()

                    st.markdown("### Результат класифікації")
                    
                    # Human-in-the-loop
                    if data.get("requires_human_review"):
                        st.error(f"**УВАГА: ПОТРЕБУЄ РУЧНОГО РЕВ'Ю**\n\n**Причина від AI:** {data.get('human_review_reason')}")
                    else:
                        st.success("Автоматична обробка дозволена")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown("**Категорія (Category)**")
                        st.info(data.get("category").upper())
                    with col2:
                        st.markdown("**Пріоритет (Priority)**")
                        prio = data.get("priority").upper()
                        if prio in ["CRITICAL", "HIGH"]:
                            st.error(f"{prio}")
                        else:
                            st.warning(prio)
                    with col3:
                        st.markdown("**Наступний крок (Next Step)**")
                        st.success(data.get("next_step").upper())

                except Exception as e:
                    st.error(f"Помилка з'єднання з сервером: {e}")

elif app_mode == "Agent Copilot (Task 2)":
    st.title("Agent Copilot")
    st.markdown("Інструмент для допомоги агентам підтримки. Згенерує саммарі, знайде правило в базі знань та запропонує 3 варіанти відповіді.")

    sample_tickets_copilot = {
        "1. Запит на рефанд (Refund)": "I bought the annual subscription 5 days ago, but I don't like the app. I want my money back.",
        "2. Технічний баг (Bug)": "Every time I try to open the profile page, the app crashes. iPhone 14 Pro.",
        "3. Скарга на експерта (Expert)": "My session with Dr. Smith was awful. He was rude, didn't listen to me and ended call early.",
        "4. Інше питання (Default)": "How do I change my password?"
    }
    
    selected_sample = st.selectbox("Оберіть шаблон для швидкого тесту (або напишіть свій):", ["(Свій текст)"] + list(sample_tickets_copilot.keys()))
    
    default_text = ""
    if selected_sample != "(Свій текст)":
        default_text = sample_tickets_copilot[selected_sample]

    ticket_text = st.text_area("Текст звернення клієнта:", value=default_text, height=150)

    if st.button("Згенерувати відповіді", type="primary"):
        if not ticket_text.strip():
            st.warning("Будь ласка, введіть текст тікету.")
        else:
            with st.spinner("Шукаю в базі знань та генерую чернетки..."):
                try:
                    response = requests.post(
                        f"{API_URL}/tickets/copilot", 
                        json={"text": ticket_text}
                    )
                    response.raise_for_status()
                    data = response.json()

                    st.markdown("---")
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.markdown("### Саммарі (Summary)")
                        st.info(data.get("summary"))
                    
                    with col2:
                        st.markdown("### Знайдено в Базі Знань")
                        st.warning(f"**Knowledge Base Match:**\n\n{data.get('kb_citation')}")

                    st.markdown("---")
                    st.markdown("### Варіанти відповідей")
                    
                    st.error("**УВАГА:** ШІ не має доступу до білінгу клієнта. Обов'язково перевірте реальний статус акаунту перед відправкою обіцянок. Відредагуйте текст за потреби.")

                    for reply in data.get("replies", []):
                        tone = reply.get("tone")
                        text = reply.get("text")
                        
                        st.text_area(f"Тон: {tone}", value=text, height=120)

                except Exception as e:
                    st.error(f"Помилка з'єднання з сервером: {e}")