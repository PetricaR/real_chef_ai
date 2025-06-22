import streamlit as st
from .security import (
    verify_password,
    create_user,
    verify_otp,
    reset_2fa,
    generate_qr,
    get_db_connection,
)
from auth.gcp_manager import GCPManager


class AuthManager:
    def __init__(self):
        self.gcp_manager = GCPManager()
        self.allowed_emails = self.gcp_manager.fetch_allowed_emails()

    def handle_authentication(self):
        if st.session_state.login_step == "username_password":
            self._handle_username_password()
        elif st.session_state.login_step == "register":
            self._handle_registration()
        elif st.session_state.login_step == "2fa":
            self._handle_2fa()

    def _handle_username_password(self):
        st.markdown(
            '<div class="stHeader">Pasul 1: Login cu username și parolă</div>',
            unsafe_allow_html=True,
        )
        username = st.text_input("Username")
        password = st.text_input("Parolă", type="password")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login"):
                if verify_password(username, password):
                    st.session_state.current_user = username
                    st.session_state.login_step = "2fa"
                    st.success("Credențiale corecte! Trecem la verificarea 2FA")
                    st.rerun()
                else:
                    st.error("Credențiale invalide!")
        with col2:
            if st.button("Înregistrare"):
                st.session_state.login_step = "register"
                st.rerun()

    def _handle_registration(self):
        st.markdown(
            '<div class="stHeader">Înregistrare utilizator nou</div>',
            unsafe_allow_html=True,
        )
        new_username = st.text_input("Username nou")
        new_email = st.text_input("Adresă de email")
        new_password = st.text_input("Parolă nouă", type="password")
        confirm_password = st.text_input("Confirmă parola", type="password")

        if st.button("Înregistrează"):
            if new_password == confirm_password:
                if new_email in self.allowed_emails:
                    try:
                        create_user(new_username, new_email, new_password)
                        st.success(
                            "Utilizator înregistrat cu succes! Te poți autentifica acum."
                        )
                        st.session_state.login_step = "username_password"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Eroare la înregistrare: {str(e)}")
                else:
                    st.error("Adresa de email nu este permisă pentru înregistrare!")
            else:
                st.error("Parolele nu coincid!")

    def _handle_2fa(self):
        st.markdown(
            f'<div class="stHeader">Pasul 2: Verificare cod 2FA pentru {st.session_state.current_user}</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Resetează 2FA"):
                reset_2fa(st.session_state.current_user)
                st.success("2FA resetat! Se va genera un nou cod QR.")
                st.rerun()
        with col2:
            if st.button("Înapoi la login"):
                st.session_state.login_step = "username_password"
                st.session_state.current_user = None
                st.rerun()

        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            "SELECT two_fa_enabled FROM users WHERE username = ?",
            (st.session_state.current_user,),
        )
        two_fa_enabled = c.fetchone()[0]
        conn.close()

        if not two_fa_enabled:
            self._handle_2fa_setup()
        else:
            self._handle_2fa_verification()

    def _handle_2fa_setup(self):
        st.info("Configurare 2FA necesară")
        st.write("1. Scanați acest cod QR cu Google Authenticator:")
        qr = generate_qr(st.session_state.current_user)
        st.image(qr)

        st.write("2. Introduceți codul pentru verificare:")
        setup_code = st.text_input("Cod de verificare", key="setup_code")

        if st.button("Verifică și activează 2FA"):
            if verify_otp(st.session_state.current_user, setup_code):
                conn = get_db_connection()
                c = conn.cursor()
                c.execute(
                    "UPDATE users SET two_fa_enabled = 1 WHERE username = ?",
                    (st.session_state.current_user,),
                )
                conn.commit()
                conn.close()
                st.session_state.is_authenticated = True
                st.success("2FA configurat cu succes!")
                st.rerun()
            else:
                st.error("Cod invalid! Încercați din nou.")

    def _handle_2fa_verification(self):
        st.write("Introduceți codul din Google Authenticator:")
        otp_code = st.text_input("Cod 2FA", key="otp_code")
        if st.button("Verifică"):
            if verify_otp(st.session_state.current_user, otp_code):
                st.session_state.is_authenticated = True
                st.success("Autentificare reușită!")
                st.rerun()
            else:
                st.error("Cod invalid!")

    def logout(self):
        st.session_state.is_authenticated = False
        st.session_state.login_step = "username_password"
        st.session_state.current_user = None
        st.rerun()

    def reset_2fa(self):
        reset_2fa(st.session_state.current_user)
        st.session_state.is_authenticated = False
        st.session_state.login_step = "2fa"
        st.success("2FA resetat! Va trebui să reconfigurați.")
        st.rerun()

    def display_status(self):
        st.write(
            f"Status: {'Autentificat' if st.session_state.is_authenticated else 'Neautentificat'}"
        )
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            "SELECT two_fa_enabled FROM users WHERE username = ?",
            (st.session_state.current_user,),
        )
        two_fa_enabled = c.fetchone()[0] if st.session_state.current_user else False
        conn.close()
        st.write(f"2FA Activat: {'Da' if two_fa_enabled else 'Nu'}")
