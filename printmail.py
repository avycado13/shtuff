import imaplib
import email
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import subprocess
import os
import tempfile


def print_file(printer_name, file_path):
    subprocess.run(["lp", "-d", printer_name, file_path])


printername = os.getenv("printer")

# Connect to the email server and retrieve emails
imap_server = imaplib.IMAP4_SSL("your_email_server")
imap_server.login("your_email_address", "your_password")
imap_server.select("INBOX")
while True:
    try:
        # Calculate the date threshold (30 days ago)
        date_threshold = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")

        # Search for emails older than the date threshold
        status, email_ids = imap_server.search(None, f"BEFORE {date_threshold}")

        # Iterate over the email IDs and retrieve each email
        for email_id in email_ids[0].split():
            status, email_data = imap_server.fetch(email_id, "(RFC822)")
            raw_email = email_data[0][1]
            email_message = email.message_from_bytes(raw_email)

            # Check if there are any attachments
            if email_message.get_content_maintype() == "multipart":
                attachment_found = False
                for part in email_message.get_payload():
                    if part.get_content_disposition() == "attachment":
                        # Process the attachment
                        attachment_found = True
                        # Create a temporary file
                        temp_file = tempfile.NamedTemporaryFile(delete=False)
                        # Write the attachment data to the temporary file
                        temp_file.write(part.get_payload(decode=True))
                        # Close the temporary file
                        temp_file.close()
                        # Print the temporary file
                        print_file(printername, temp_file.name)

                if not attachment_found:
                    # Send an email to the user indicating no attachment found
                    sender_email = "your_sender_email"
                    sender_password = "your_sender_password"
                    if email_message["In-Reply-To"]:
                        recipient_email = email_message["In-Reply-To"]
                    else:
                        recipient_email = email_message["From"]

                    message = MIMEText("No attachment found in the email.")
                    message["Subject"] = "No Attachment Found"
                    message["From"] = sender_email
                    message["To"] = recipient_email

                    with smtplib.SMTP("your_smtp_server", 587) as server:
                        server.starttls()
                        server.login(sender_email, sender_password)
                        server.send_message(message)

            else:
                # Send an email to the user indicating no attachment found
                sender_email = "your_sender_email"
                sender_password = "your_sender_password"
                if email_message["In-Reply-To"]:
                    recipient_email = email_message["In-Reply-To"]
                else:
                    recipient_email = email_message["From"]

                message = MIMEText("No attachment found in the email.")
                message["Subject"] = "No Attachment Found"
                message["From"] = sender_email
                message["To"] = recipient_email

                with smtplib.SMTP("your_smtp_server", 587) as server:
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.send_message(message)

            # Delete the email
            imap_server.store(email_id, "+FLAGS", "\\Deleted")

        # Permanently remove the deleted emails
        imap_server.expunge()
    except KeyboardInterrupt:
        break
# Close the connection to the email server
imap_server.close()
imap_server.logout()
