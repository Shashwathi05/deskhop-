import smtplib
from email.mime.text import MIMEText

SENDER_EMAIL = "shashwathip2005@gmail.com"
APP_PASSWORD = "qbmq oxee vveh mepk"  # Generate from Google account

def send_verification_email(to_email, verification_link):
    msg = MIMEText(f"Click to verify your account:\n\n{verification_link}")
    msg["Subject"] = "Verify Your Deskhop Account"
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(SENDER_EMAIL, APP_PASSWORD)
    server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
    server.quit()
