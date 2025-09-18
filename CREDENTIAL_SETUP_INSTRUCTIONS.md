# 🔐 Comprehensive Credential Management System - Setup Guide

## System Overview

A complete credential management system has been implemented for the Pink Lemonade Grant Platform, providing:

- **Automated credential detection and validation**
- **Priority-based setup guidance** 
- **Real-time service status monitoring**
- **Fallback environment variable support**
- **RESTful API endpoints for credential management**

## 📊 Current Status

**Available Services (3):**
- ✅ Candid News API
- ✅ Candid Grants API  
- ✅ Flask Sessions (secure)

**High Priority Missing (2):**
- ❌ SAM.gov API Key - Federal contract opportunities
- ❌ Candid API Key - Foundation data access

**Format Issues Detected (2):**
- ⚠️ OpenAI API Key - Invalid format detected
- ⚠️ SendGrid API Key - Invalid format detected

## 🚀 Quick Setup Guide

### Step 1: Access Credential Management
Visit these endpoints to manage your credentials:

- **Status Dashboard**: `/api/credentials/status`
- **Setup Guide**: `/api/credentials/setup-guide`  
- **Missing Credentials**: `/api/credentials/missing?priority=high`

### Step 2: Priority Setup Order

#### **CRITICAL PRIORITY** (Essential for core functionality)
1. **OpenAI API Key** (`OPENAI_API_KEY`)
   - Service: AI-powered grant matching and writing
   - Setup: https://platform.openai.com/api-keys
   - Format: Must start with `sk-`

#### **HIGH PRIORITY** (Important for main features)
1. **SAM.gov API Key** (`SAM_GOV_API_KEY`)
   - Service: Federal contract opportunities and entity data
   - Setup: https://api.sam.gov/getting-started
   - Cost: Free (10,000 requests/day)

2. **Candid API Key** (`CANDID_API_KEY`)
   - Service: Foundation and nonprofit data
   - Setup: https://candid.org/about/products-services/apis
   - Cost: Subscription-based ($100-$1000+/month)

3. **SendGrid API Key** (`SENDGRID_API_KEY`)
   - Service: Email notifications and communications
   - Setup: https://sendgrid.com/docs/ui/account-and-settings/api-keys/
   - Cost: Free up to 100 emails/day
   - Format: Must start with `SG.`

### Step 3: Add Secrets in Replit

For each credential:

1. **Open Replit Secrets**:
   - Click the 🔒 "Secrets" tab in left sidebar
   - Click "New Secret" button

2. **Add Each Credential**:
   - **Key**: Use exact environment variable name (e.g., `SAM_GOV_API_KEY`)
   - **Value**: Paste your API key
   - Click "Add Secret"

3. **Restart Application**:
   - Restart your Replit to load new secrets
   - Check `/api/credentials/status` to verify

## 🔍 Verification & Testing

### Credential Status API
```bash
curl http://localhost:5000/api/credentials/status
```

### Test Specific Credential
```bash
curl http://localhost:5000/api/credentials/validate/sam_gov_api_key
```

### View Enabled Services
```bash
curl http://localhost:5000/api/credentials/services/enabled
```

## 🛠️ Advanced Configuration

### Environment Variable Mapping

| Service | Primary Variable | Fallback Variables |
|---------|-----------------|-------------------|
| OpenAI | `OPENAI_API_KEY` | `OPENAI_KEY`, `AI_API_KEY` |
| SAM.gov | `SAM_GOV_API_KEY` | `SAM_API_KEY`, `SAMGOV_KEY` |
| Candid | `CANDID_API_KEY` | `CANDID_KEY`, `FOUNDATION_CENTER_KEY` |
| SendGrid | `SENDGRID_API_KEY` | `SENDGRID_KEY`, `EMAIL_API_KEY` |

### Validation Rules

- **OpenAI**: Must start with `sk-`, minimum 48 characters
- **SendGrid**: Must start with `SG.`, minimum 43 characters
- **SAM.gov**: Minimum 32 characters
- **Candid**: Minimum 20 characters

## 🚨 Troubleshooting

### Invalid API Key Format
- Double-check you copied the entire key
- Verify no extra spaces or characters
- Check required prefixes (`sk-`, `SG.`)

### Authentication Errors (401/403)
- Verify API key is active and not expired
- Check account permissions with service provider
- Ensure using production key, not test key

### Rate Limiting (429 Errors)
- Check API usage limits
- Consider upgrading service plan
- Monitor usage patterns

### Secret Not Loading
- Ensure secret name exactly matches variable name
- Restart Replit application after adding secrets
- Check Secrets tab to confirm secret was saved

## 📈 Service Impact by Credential

### With SAM.gov API Key:
- Access to federal contract opportunities
- Government entity registration data
- Compliance and vendor information

### With Candid API Key:
- Foundation directory and profiles
- Grant opportunity matching
- Philanthropic data and insights

### With SendGrid API Key:
- Email notifications for grant deadlines
- Team collaboration invitations
- Application status updates

## 🔄 Incremental Setup

The system is designed for **incremental credential addition**:

1. **Start with free credentials** (SAM.gov)
2. **Add communication** (SendGrid free tier)
3. **Upgrade to premium services** (Candid, Zyte)
4. **Monitor usage and costs**

## 📞 Support

- **API Documentation**: Each credential has setup URLs and validation info
- **Real-time Status**: Use `/api/credentials/status` endpoint
- **Service Health**: Monitor application logs for credential errors

---

**System Status**: ✅ Fully Operational  
**Last Updated**: September 18, 2025  
**Version**: 1.0.0