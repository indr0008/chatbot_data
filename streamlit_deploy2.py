from operator import itemgetter
import streamlit as st
import re
from ast import literal_eval

from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_core.runnables import RunnablePassthrough
from langchain_community.utilities import SQLDatabase

from config_env import *
from prompt_vault import response_prompt, query_routing_prompt, result_nl2sql_prompt, nl2sql_prompt, privacy_handling_message
from langchain.globals import set_verbose

set_verbose(True)
st.set_page_config(page_title="Mita - Your Mandiri Partner", 
                   layout="wide"
                   )
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] > div:first-child {
        display: flex;
        flex-direction: column;
        justify-content: center;
        height: 100vh;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

st.sidebar.title("Enter User CIF")
user_cif = st.sidebar.text_input("Enter CIF:"   )

# Initialize models and vector store
embedding_model = AzureOpenAIEmbeddings(azure_endpoint=embedding_endpoint, api_key=api_key)
vector_store = InMemoryVectorStore(embedding_model).load(vector_store_name, embedding_model)
db = SQLDatabase.from_uri("sqlite:///rag_base.db")


low_temp_llm = AzureChatOpenAI(
    openai_api_version=azure_openai_version,
    azure_endpoint=llm_endpoint,
    temperature=low_temp_param,
    api_key=api_key
)
high_temp_llm = AzureChatOpenAI(temperature=high_temp_param, 
                                openai_api_version=azure_openai_version,
                                azure_endpoint=llm_endpoint,
                                api_key=api_key
                               )

def decisioning_chain():
    chain =  (
        {
            "question": RunnablePassthrough(),
        }
        | query_routing_prompt
        | low_temp_llm
    )
    return chain

def chain_prompt_1():
    def privacy_handling(sql_result):
        result = ""
        if sql_result.content == "PRIVACY ALERT":
            return privacy_handling_message
        else:
            try:
                # Clean up and format the SQL query
                query = sql_result.content.replace("`",'').replace("sql","").strip()
                query = query.strip()
                print("query: -->", query)
                
                # Identify query type (SELECT, INSERT, DELETE)
                query_type = query.split()[0].upper()

                # Use db.run for executing queries
                if query_type == "SELECT":
                    # Handle SELECT query
                    result = db.run(query)
                    print("result: -->", result)
                elif query_type == "INSERT" or query_type == "DELETE" or query_type == "UPDATE":
                    # Handle INSERT or DELETE query
                    db.run(query)
                    result = f"{query_type} query executed successfully."
                    print("result: -->", result)
                else:
                    result = "Unsupported query type"
                
                return result
            
            except BaseException as e:
                print(e)
                return "EMPTY_STRING"

    nl2sql_chain = (
        {
            "question": itemgetter("question"),
            "cif": itemgetter("cif"),
            "nama_nasabah": itemgetter("nama_nasabah"),
            "chat_history": itemgetter("chat_history")
        }
        | nl2sql_prompt
        | low_temp_llm
        | 
        {
            "sql_result": lambda x: privacy_handling(x),
            "nama_nasabah": RunnablePassthrough(),
            "question": RunnablePassthrough(),
        }
        | result_nl2sql_prompt
        | high_temp_llm
    )
    return nl2sql_chain


def chain_prompt_2(vectorstore):
    chain = (
        {
            "question": itemgetter("question"),
            "chat_history": itemgetter("chat_history"),
            "context": lambda x: vectorstore.similarity_search(x["question"], 
                                                               k=similarity_search_k, 
                                                               similarity_threshold = similarity_search_threshold, 
                                                               alpha = similarity_search_alpha),
        }
        | response_prompt
        | low_temp_llm
    )
    return chain

# Predefined responses
RESPONSES = {
    'id': {
        'greeting': "👋 Hai! Saya Mita, asisten layanan pelanggan Bank Mandiri. Untuk memberikan pelayanan terbaik silahkan bertanya atau beri saya instruksi",
        'short_greeting': "👋 Hai! Saya Mita, asisten layanan pelanggan Bank Mandiri.",
        'language_prompt': "Untuk memberikan pelayanan terbaik, apakah Anda lebih nyaman menggunakan Bahasa Indonesia atau English?",
        'irrelevant': "Maaf, pertanyaan tersebut tidak relevan dengan produk atau layanan Bank Mandiri. Silakan ajukan pertanyaan lain seputar layanan kami!",
        'error': "Maaf, terjadi kesalahan dalam memproses permintaan Anda. Silakan coba lagi.",
        'clarification': "Mohon maaf, saya kurang memahami maksud Anda. Bisakah Anda menjelaskan lebih detail?",
    },
    'en': {
        'greeting': "👋 Hi! I'm Mita, Bank Mandiri's customer service assistant. To provide the best service, please give me instruction or ask anything",
        'short_greeting': "👋 Hi! I'm Mita, Bank Mandiri's customer service assistant.",
        'language_prompt': "To provide the best service, would you prefer to communicate in Bahasa Indonesia or English?",
        'irrelevant': "I apologize, but that question isn't relevant to Bank Mandiri's products or services. Please feel free to ask about our services!",
        'error': "I apologize, but there was an error processing your request. Please try again.",
        'clarification': "I'm sorry, I didn't quite understand. Could you please elaborate?",
    }
}

def detect_language_preference(text):
    """Simple language detection based on common words"""
    # For simplicity, we're always returning 'id' here. In a real implementation,
    # you'd want to implement actual language detection logic.
    return 'id'

def get_response(key, lang='id'):
    """Get response in the specified language"""
    return RESPONSES[lang][key]

def get_nama_nasabah(database, cif):
    nama_nasabah = database.run(f"select nama_lengkap from informasi_kartu_kredit where cif = {cif} limit 1")
    if nama_nasabah:
        nama_nasabah = literal_eval(nama_nasabah)
        if nama_nasabah:
            return nama_nasabah[0][0]



#==================================================================================================================================================================
# Streamlit Session

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "language_set" not in st.session_state:
    st.session_state.language_set = False
if "selected_language" not in st.session_state:
    st.session_state.selected_language = None



# Streamlit UI
st.markdown(
    """
    <style>
    .custom-title {
        font-size: 72px; /* Adjust the size here */
        font-weight: bold;
        color: #333333;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

# Applying the custom title
st.markdown('<h1 class="custom-title">Mita by Mandiri</h1>', unsafe_allow_html=True)
st.markdown("**Your Trusted Guide to All Things Mandiri: Quick, Accurate, Personalized.**")

cifno = None
nama_nasabah = None


# Initialize the RAG chain
if user_cif:
    cifno = user_cif
    nama_nasabah = get_nama_nasabah(database=db, 
                                    cif=cifno)

print(cifno, nama_nasabah)    
chain_1 = chain_prompt_1()
chain_2 = chain_prompt_2(vector_store)
main_chain = decisioning_chain()

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# User input handling
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", 
                                      "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
        if not st.session_state.language_set:
            detected_lang = detect_language_preference(prompt)
            st.session_state.selected_language = detected_lang
            st.session_state.language_set = True
      

    lang = st.session_state.selected_language

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = main_chain.invoke({"question": prompt})
            print(prompt, response.content)
            try:
                if response.content == "PROMPT_1":
                    response = chain_1.invoke({"question": prompt, 
                                               "cif": cifno,
                                               "nama_nasabah": nama_nasabah,
                                               "chat_history": st.session_state.messages[-10:]})

                else:
                    # Generate response using RAG
                    response = chain_2.invoke({"question": prompt, 
                                                "chat_history": st.session_state.messages[-10:]
                                                })

                # Check for irrelevant questions
                if "tidak relevan" in response.content.lower() or "not relevant" in response.content.lower():
                    st.markdown(get_response('irrelevant', lang))
                else:
                    st.markdown(response.content)
                
                # Add response to history
                st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response.content
                    })

            except Exception as e:
                st.error(get_response('error', lang))
                print(f"Error: {str(e)}")  # For debugging

