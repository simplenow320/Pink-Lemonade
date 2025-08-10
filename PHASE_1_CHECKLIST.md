# PHASE 1: Authentication & Core Implementation
## Day 1-5 Checklist

### Day 1: Registration Form ⏳
- [ ] Create `app/templates/auth/register.html`
- [ ] Build registration API endpoint
- [ ] Add form validation (email, password strength)
- [ ] Implement user creation in database
- [ ] Test registration flow

### Day 2: Login System ⏳
- [ ] Create `app/templates/auth/login.html`
- [ ] Build login API endpoint
- [ ] Implement JWT token generation
- [ ] Add remember me functionality
- [ ] Create logout endpoint

### Day 3: Password Reset ⏳
- [ ] Create `app/templates/auth/forgot_password.html`
- [ ] Build password reset request endpoint
- [ ] Generate secure reset tokens
- [ ] Create `app/templates/auth/reset_password.html`
- [ ] Implement password update endpoint

### Day 4: Email Verification ⏳
- [ ] Set up email service (SendGrid/SMTP)
- [ ] Create verification email template
- [ ] Generate verification tokens
- [ ] Build verification endpoint
- [ ] Add resend verification option

### Day 5: Profile Uploads ⏳
- [ ] Add file upload to profile page
- [ ] Support PDF/DOC/DOCX formats
- [ ] Implement secure file storage
- [ ] Add 501(c)(3) verification field
- [ ] Create document preview feature

---

## Code Templates to Start With

### 1. Registration Form (register.html)
```html
{% extends "base.html" %}
{% block title %}Register - Pink Lemonade{% endblock %}
{% block content %}
<div class="auth-container">
  <h2>Create Your Account</h2>
  <form id="registerForm" method="POST" action="/api/auth/register">
    <div class="form-group">
      <label>Organization Name</label>
      <input type="text" name="org_name" required>
    </div>
    <div class="form-group">
      <label>Email Address</label>
      <input type="email" name="email" required>
    </div>
    <div class="form-group">
      <label>Password</label>
      <input type="password" name="password" required>
      <small>Minimum 8 characters, include numbers and symbols</small>
    </div>
    <div class="form-group">
      <label>Confirm Password</label>
      <input type="password" name="confirm_password" required>
    </div>
    <button type="submit" class="btn-primary">Create Account</button>
  </form>
</div>
{% endblock %}
```

### 2. Auth Service (auth_service.py)
```python
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
import secrets

class AuthService:
    def __init__(self, app):
        self.app = app
        self.secret_key = app.config['SECRET_KEY']
    
    def register_user(self, email, password, org_name):
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            org_name=org_name,
            verified=False
        )
        
        # Generate verification token
        token = self.generate_verification_token(email)
        
        # Send verification email
        self.send_verification_email(email, token)
        
        return user
    
    def generate_jwt(self, user_id):
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=7)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['user_id']
        except:
            return None
```

### 3. Email Service (email_service.py)
```python
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class EmailService:
    def __init__(self):
        self.sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        self.from_email = 'noreply@pinklemonade.app'
    
    def send_verification_email(self, to_email, token):
        verification_url = f"https://pinklemonade.app/verify?token={token}"
        
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject='Verify Your Pink Lemonade Account',
            html_content=f'''
            <h2>Welcome to Pink Lemonade!</h2>
            <p>Click the link below to verify your email:</p>
            <a href="{verification_url}" class="button">Verify Email</a>
            <p>This link expires in 24 hours.</p>
            '''
        )
        
        response = self.sg.send(message)
        return response.status_code == 202
```

---

## Testing Checklist

### Unit Tests
- [ ] Test user registration
- [ ] Test login with valid/invalid credentials
- [ ] Test password reset flow
- [ ] Test email verification
- [ ] Test file upload

### Integration Tests
- [ ] Full registration → login flow
- [ ] Password reset → new login
- [ ] Email verification → account activation
- [ ] Profile upload → storage verification

### Security Tests
- [ ] SQL injection attempts
- [ ] XSS in forms
- [ ] CSRF protection
- [ ] Password strength validation
- [ ] Token expiration

---

## Definition of Done

✅ Phase 1 is complete when:
1. Users can register with email/password
2. Users can login and receive JWT token
3. Users can reset forgotten passwords
4. Email verification is required and working
5. Organization documents can be uploaded
6. All tests pass with >90% coverage
7. No security vulnerabilities found
8. Documentation is updated

---

*Start Date: [Today]*
*Target Completion: [5 days from today]*
*Status: Ready to Begin*