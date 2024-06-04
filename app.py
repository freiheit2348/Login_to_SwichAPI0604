import os
import openai
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from fastapi import FastAPI, HTTPException, Depends, Request, Form
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, HTMLResponse
from authlib.integrations.starlette_client import OAuth, OAuthError
from pydantic import BaseModel
from passlib.context import CryptContext
import gradio as gr
import json
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Replace these with your own OAuth settings
GOOGLE_CLIENT_ID = "90335848003-dro5aadok8pa8tlvi5pjanbful32clsu.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
SECRET_KEY = "0af44a376fcc9ed9d760f035c5c0dd9cd76e127853c71c8f98d5968bf24ae590"
USER_DATA_FILE = "C:\\Users\\OWNER\\Desktop\\NewProject\\0604\\Login\\registered_users.json"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("GMAIL_ADDRESS")
SMTP_PASSWORD = os.getenv("GMAIL_PASSWORD")

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Configure OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    username: str
    hashed_password: str

# ユーザーデータの読み込みと保存
def load_users():
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f)

registered_users = load_users()

def get_user(request: Request):
    user = request.session.get('user')
    if user:
        return user['email']
    return None

def send_reset_email(email, reset_link):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USERNAME
    msg['To'] = email
    msg['Subject'] = "Password Reset Request"
    body = f"Click the following link to reset your password: {reset_link}"
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    text = msg.as_string()
    server.sendmail(SMTP_USERNAME, email, text)
    server.quit()

@app.get('/')
async def homepage(request: Request):
    user = request.session.get('user')
    if user:
        return HTMLResponse(
            f'<h1>Welcome {user["name"]}</h1>'
            f'<a href="/logout">Logout</a><br>'
            f'<a href="/gradio">Go to Gradio App</a><br>'
            f'<a href="/signup">Sign Up</a><br>'
            f'<a href="/reset_request">Forgot Password?</a>'
        )
    return HTMLResponse('<a href="/login">Login with Google</a><br><a href="/signup">Sign Up</a>')

@app.route('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.route('/auth')
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    user_info = token.get('userinfo')
    if user_info:
        request.session['user'] = dict(user_info)
    return RedirectResponse(url='/post_auth')

@app.get('/post_auth')
async def post_auth(request: Request):
    user = request.session.get('user')
    if user:
        # 常に /gradio へリダイレクト
        return RedirectResponse(url='/gradio')
    return RedirectResponse(url='/')

@app.route('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')

@app.get('/signup')
async def signup_form(request: Request):
    user = request.session.get('user')
    if user:
        # 既にユーザー名とパスワードが設定されている場合は、フォームを表示しない
        if user['email'] in registered_users:
            return HTMLResponse(f"<h1>既に登録済みです。</h1><a href='/gradio'>Go to Gradio App</a>")
        else:
            return HTMLResponse(f"""
                <form action="/signup" method="post">
                    Username: <input type="text" name="username"><br>
                    Password: <input type="password" name="password"><br>
                    <input type="submit" value="Sign Up">
                </form>
            """)
    else:
        return RedirectResponse(url='/')

@app.post('/signup')
async def signup(request: Request, username: str = Form(), password: str = Form()):
    user = request.session.get('user')
    if user:
        if user['email'] not in registered_users:
            hashed_password = pwd_context.hash(password)
            registered_users[user['email']] = {"username": username, "hashed_password": hashed_password}
            save_users(registered_users)
        return RedirectResponse(url='/gradio')
    return RedirectResponse(url='/')

@app.get('/reset_request')
async def reset_request_form(request: Request):
    return HTMLResponse(f"""
        <form action="/reset_request" method="post">
            Enter your email to reset password: <input type="email" name="email"><br>
            <input type="submit" value="Send Reset Link">
        </form>
    """)

@app.post('/reset_request')
async def reset_request(request: Request, email: str = Form()):
    if email in registered_users:
        reset_link = f"http://127.0.0.1:8000/reset_password?email={email}"
        send_reset_email(email, reset_link)
        return HTMLResponse("Password reset link has been sent to your email.")
    return HTMLResponse("Email not found!")

@app.get('/reset_password')
async def reset_password_form(request: Request, email: str):
    return HTMLResponse(f"""
        <form action="/reset_password" method="post">
            <input type="hidden" name="email" value="{email}">
            New Password: <input type="password" name="new_password"><br>
            <input type="submit" value="Reset Password">
        </form>
    """)

@app.post('/reset_password')
async def reset_password(request: Request, email: str = Form(), new_password: str = Form()):
    if email in registered_users:
        hashed_password = pwd_context.hash(new_password)
        registered_users[email]['hashed_password'] = hashed_password
        save_users(registered_users)
        return HTMLResponse("Password reset successfully!")
    return HTMLResponse("User not found!")

# Gradio app
def login_interface(username, password, request: gr.Request):
    user = request.session.get('user')
    if user:
        if user['email'] in registered_users:
            if username == registered_users[user['email']]['username']:
                if pwd_context.verify(password, registered_users[user['email']]['hashed_password']): 
                    return gr.update(visible=False), gr.update(visible=True), "Login successful"
                else:
                    return gr.update(visible=True), gr.update(visible=False), "パスワードが間違っています。"
            else:
                return gr.update(visible=True), gr.update(visible=False), "ユーザーネームが間違っています。"
        else:
            return gr.update(visible=True), gr.update(visible=False), "ユーザーは登録されていません。"
    else:
        return gr.update(visible=True), gr.update(visible=False), "Google で認証してください。"

def query_interface(platform, api_key, user_question):
    if platform == "OpenAI":
        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_question},
            ],
        )
        return response.choices[0].message.content
    elif platform == "Anthropic":
        anthropic = Anthropic(api_key=api_key)
        response = anthropic.completions.create(
            model="claude-v1",
            prompt=f"{HUMAN_PROMPT} {user_question} {AI_PROMPT}",
            max_tokens_to_sample=1024
        )
        return response.completion
    elif platform == "Gemini":
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(user_question)
        return response.text
    else:
        return f"API call for {platform} is not implemented yet."

with gr.Blocks() as demo:
    with gr.Row(visible=True) as login_row:
        username = gr.Textbox(label="Username")
        password = gr.Textbox(label="Password", type="password")
        login_button = gr.Button("Login")
        login_message = gr.Textbox(label="Login Message", interactive=False)

    with gr.Row(visible=False) as query_row:
        platform = gr.Radio(choices=["OpenAI", "Anthropic", "Gemini"], label="Select Platform")
        api_key = gr.Textbox(label="API Key", type="password", lines=1)
        user_question = gr.Textbox(label="Enter your question", lines=2, placeholder="Type your question here...")
        query_button = gr.Button("Submit")
        response = gr.Textbox(label="AI Response", interactive=False)
    
    login_button.click(login_interface, inputs=[username, password], outputs=[login_row, query_row, login_message])
    query_button.click(query_interface, inputs=[platform, api_key, user_question], outputs=response)

app = gr.mount_gradio_app(app, demo, path="/gradio", auth_dependency=get_user)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)