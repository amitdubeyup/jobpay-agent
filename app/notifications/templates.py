from jinja2 import Environment, DictLoader
from typing import Dict, Any


# Email templates
EMAIL_TEMPLATES = {
    "job_match": """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: #4CAF50; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; background: #f9f9f9; }
            .job-details { background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }
            .skills { background: #e8f5e9; padding: 10px; margin: 10px 0; border-radius: 3px; }
            .cta { text-align: center; margin: 20px 0; }
            .button { background: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 New Job Match Found!</h1>
            </div>
            <div class="content">
                <p>Hi {{ candidate_name }},</p>
                
                <p>Great news! We found a job that matches your skills and preferences:</p>
                
                <div class="job-details">
                    <h2>{{ job_title }}</h2>
                    <p><strong>Company:</strong> {{ company }}</p>
                    <p><strong>Location:</strong> {{ location }}</p>
                    {% if salary_range %}
                    <p><strong>Salary:</strong> {{ salary_range }}</p>
                    {% endif %}
                    <p><strong>Job Type:</strong> {{ job_type }}</p>
                </div>
                
                <div class="skills">
                    <h3>🎯 Why you're a great match:</h3>
                    <ul>
                    {% for strength in match_strengths %}
                        <li>{{ strength }}</li>
                    {% endfor %}
                    </ul>
                    
                    {% if matching_skills %}
                    <p><strong>Your matching skills:</strong> {{ matching_skills|join(', ') }}</p>
                    {% endif %}
                </div>
                
                <div class="cta">
                    <a href="{{ application_url }}" class="button">Apply Now</a>
                </div>
                
                <p>Best regards,<br>The JobPay Team</p>
            </div>
        </div>
    </body>
    </html>
    """,
    
    "welcome_candidate": """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: #2196F3; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to JobPay! 🚀</h1>
            </div>
            <div class="content">
                <p>Hi {{ candidate_name }},</p>
                
                <p>Welcome to JobPay! We're excited to help you find your dream job.</p>
                
                <p>Your profile has been created successfully. Our AI-powered matching system will now start looking for jobs that match your skills and preferences.</p>
                
                <p>You'll receive notifications when we find relevant opportunities for you.</p>
                
                <p>Best regards,<br>The JobPay Team</p>
            </div>
        </div>
    </body>
    </html>
    """,
    
    "job_posted": """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: #FF9800; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Job Posted Successfully! 📢</h1>
            </div>
            <div class="content">
                <p>Hi {{ employer_name }},</p>
                
                <p>Your job posting "{{ job_title }}" has been successfully published!</p>
                
                <p>Our AI matching system is now analyzing candidate profiles to find the best matches for your position.</p>
                
                <p>You'll receive updates as candidates are matched and apply for your position.</p>
                
                <p>Best regards,<br>The JobPay Team</p>
            </div>
        </div>
    </body>
    </html>
    """
}


# SMS templates
SMS_TEMPLATES = {
    "job_match": "🎯 JobPay: New job match! {{ job_title }} at {{ company }}. Match score: {{ match_score }}%. Apply: {{ application_url }}",
    "welcome_candidate": "Welcome to JobPay! Your profile is active and we're searching for jobs that match your skills. You'll get notified about opportunities.",
    "job_posted": "JobPay: Your job '{{ job_title }}' is now live! Our AI is finding the best candidates for you."
}


# WhatsApp templates (similar to SMS but can be longer)
WHATSAPP_TEMPLATES = {
    "job_match": """🎯 *New Job Match Found!*

*{{ job_title }}* at *{{ company }}*
📍 {{ location }}
💰 {{ salary_range }}
🎯 Match Score: {{ match_score }}%

*Why you're a great fit:*
{{ match_summary }}

Apply now: {{ application_url }}

- JobPay Team""",
    
    "welcome_candidate": """🚀 *Welcome to JobPay!*

Hi {{ candidate_name }}, your profile is now active!

Our AI-powered system is searching for jobs that match your skills and preferences. You'll receive notifications when we find relevant opportunities.

Good luck with your job search! 🍀

- JobPay Team""",
    
    "job_posted": """📢 *Job Posted Successfully!*

Your job posting "{{ job_title }}" is now live!

Our AI is analyzing candidate profiles to find the best matches. You'll receive updates as candidates are matched.

- JobPay Team"""
}


# Push notification templates
PUSH_TEMPLATES = {
    "job_match": {
        "title": "🎯 New Job Match!",
        "body": "{{ job_title }} at {{ company }} - {{ match_score }}% match"
    },
    "welcome_candidate": {
        "title": "Welcome to JobPay!",
        "body": "Your profile is active. We're finding jobs for you!"
    },
    "job_posted": {
        "title": "Job Posted!",
        "body": "{{ job_title }} is now live and being matched"
    }
}


class TemplateManager:
    """Manages notification templates across different channels."""
    
    def __init__(self):
        self.email_env = Environment(loader=DictLoader(EMAIL_TEMPLATES))
        self.sms_env = Environment(loader=DictLoader(SMS_TEMPLATES))
        self.whatsapp_env = Environment(loader=DictLoader(WHATSAPP_TEMPLATES))
    
    def render_email(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render email template."""
        template = self.email_env.get_template(template_name)
        return template.render(**context)
    
    def render_sms(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render SMS template."""
        template = self.sms_env.get_template(template_name)
        return template.render(**context)
    
    def render_whatsapp(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render WhatsApp template."""
        template = self.whatsapp_env.get_template(template_name)
        return template.render(**context)
    
    def render_push(self, template_name: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Render push notification template."""
        template_data = PUSH_TEMPLATES.get(template_name, {})
        
        env = Environment()
        
        return {
            "title": env.from_string(template_data.get("title", "")).render(**context),
            "body": env.from_string(template_data.get("body", "")).render(**context)
        }
