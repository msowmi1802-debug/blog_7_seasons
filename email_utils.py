import os
import smtplib

from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()


EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def send_otp_email(receiver_email, otp):

    message = EmailMessage()

    message["Subject"] = "Your 7_Seasons OTP"

    message["From"] = EMAIL_ADDRESS

    message["To"] = receiver_email

    message.set_content(
        f"""
Hello,

Your OTP is:

{otp}

This OTP is valid for 2 minutes.

Do not share it with anyone.

- 7_Seasons
"""
    )

    with smtplib.SMTP("smtp.gmail.com", 587,timeout=10) as smtp:

        smtp.starttls()

        smtp.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD,
        )

        smtp.send_message(message)
