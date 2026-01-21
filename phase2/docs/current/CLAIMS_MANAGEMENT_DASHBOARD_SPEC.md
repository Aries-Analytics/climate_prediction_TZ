# Claims Management Dashboard - Technical Specification

## Overview

The **Claims Management Dashboard** is a dedicated interface for managing automated parametric insurance claims triggered by climate index events. This dashboard handles the complete lifecycle from trigger approval to payment disbursement and farmer notification.

## Business Context

### Parametric vs Traditional Claims

**Traditional Insurance Claims:**
- Farmer files a claim after crop damage
- Adjuster visits farm to assess loss
- Manual approval process (days/weeks)
- Payment after verification

**Parametric Insurance Claims (This System):**
- Automatically triggered when index breaches threshold
- No farm visit required (satellite/weather data)
- Automated calculation based on contract terms
- Rapid disbursement (hours/days)

**Regulatory Note:** Despite automation, these are still classified as **insurance claims** by regulatory bodies (TIRA) and must be tracked, audited, and reported as such.

---

## Dashboard Sections

### 1. Claims Overview (KPI Cards)

**Metrics:**
- **Total Claims (Current Month)**: Count of all triggered claims
- **Pending Approval**: Claims awaiting manual authorization
- **Processing**: Claims in payment pipeline
- **Disbursed**: Successfully paid claims
- **Failed**: Payments requiring retry
- **Total Claim Value**: Aggregate amount disbursed

**Visual:**
- Color-coded cards (Green: Success, Yellow: Pending, Red: Failed)
- Trend indicators (↑↓ vs previous month)

---

### 2. Claims Registry (Data Table)

**Purpose:** Complete audit trail of all claims

**Columns:**
| Column | Description | Data Type |
|--------|-------------|-----------|
| Claim ID | Unique identifier | Auto-increment |
| Farmer ID | Policyholder reference | String |
| Farmer Name | Full name | String |
| Location | Village/District | String |
| Trigger Type | Drought/Flood/Crop Failure | Enum |
| Trigger Date | Date index threshold breached | Date |
| Claim Amount | Calculated payout (USD) | Currency |
| Status | Pending/Approved/Processing/Disbursed/Failed | Status Badge |
| Payment Method | M-Pesa/Bank/Mobile Money | String |
| Transaction ID | Gateway confirmation ID | String |
| Disbursement Date | Date payment completed | Date/Time |
| Actions | View Details / Retry Payment | Buttons |

**Features:**
- **Filtering:** By status, date range, location, trigger type
- **Sorting:** Any column
- **Search:** Farmer name, ID, transaction ID
- **Export:** CSV/Excel for regulatory reporting
- **Pagination:** 50 rows per page

**Status Color Coding:**
- 🟡 Pending: Awaiting approval
- 🔵 Approved: Authorization confirmed, payment queued
- 🟠 Processing: In payment gateway
- 🟢 Disbursed: Successfully paid
- 🔴 Failed: Payment error, requires retry

---

### 3. Approval Workflow

**Trigger:**
When admin clicks "Approve Payout Batch" on Trigger Events Dashboard

**Process:**
1. System fetches all active triggers (probability ≥75%)
2. For each trigger:
   - Query farmer registry for affected farmers
   - Calculate claim amount using payout formula:
     ```
     Claim Amount = Base Rate × Severity Multiplier
     - Drought: $60 × (Deficit / Threshold)
     - Flood: $75 × (Excess / Threshold)
     - Crop Failure: $90 × Probability
     ```
3. Create claim records in database
4. Generate batch approval summary:
   - Total farmers affected: X
   - Total claim amount: $Y
   - Breakdown by trigger type

**Approval UI:**
- Summary card with totals
- Confirmation dialog: "Approve disbursement of $X to Y farmers?"
- Checkbox: "I confirm index data has been validated"
- Actions: Approve / Cancel

**Backend:**
```
POST /api/claims/approve-batch
Body: {
  trigger_ids: [1, 2, 3],
  approved_by: user_id,
  approval_notes: string
}
```

---

### 4. Payment Processing Queue

**Purpose:** Monitor real-time payment status

**Display:**
- Progress bar: "Processing 45/100 payments"
- Live status updates for each payment
- Error alerts for failed transactions

**Integration Points:**
- **M-Pesa API** (Tanzania - Vodacom)
- **Tigo Pesa** (Alternative provider)
- **Bank Transfer** (For larger payouts)

**Payment Flow:**
1. Claim moves to "Processing" status
2. Backend calls payment gateway API
3. Gateway returns transaction ID
4. System polls gateway for confirmation (webhook preferred)
5. On success: Update status to "Disbursed"
6. On failure: Log error, move to "Failed" queue

**Retry Logic:**
- Automatic: 3 retries with exponential backoff
- Manual: "Retry Payment" button in Claims Registry
- Escalation: Flag for manual review after 3 failures

---

### 5. Farmer Notifications

**Purpose:** Communication log and delivery tracking

**Table Columns:**
| Column | Description |
|--------|-------------|
| Farmer | Name + Phone |
| Notification Type | SMS / Email / App Push |
| Trigger | Drought / Flood / Crop Failure |
| Message Content | "Your claim of $X has been approved..." |
| Status | Sent / Delivered / Failed |
| Sent At | Timestamp |
| Actions | Resend |

**Message Templates:**

**Claim Approved:**
```
Habari [Farmer Name],
Your parametric insurance claim of TZS [Amount] has been approved 
due to [Trigger Type] on [Date]. Payment will be disbursed within 
24 hours to [Phone Number].
- Morogoro Rice Pilot
```

**Payment Confirmed:**
```
Habari [Farmer Name],
TZS [Amount] has been sent to your M-Pesa account ([Phone]). 
Transaction ID: [Transaction ID]. Use funds for replanting or 
emergency needs.
- Morogoro Rice Pilot
```

**Payment Failed:**
```
Habari [Farmer Name],
There was an issue processing your claim payment. Our team 
will contact you within 24 hours to resolve. Reference: [Claim ID].
- Morogoro Rice Pilot
```

**Integration:**
- **Africa's Talking SMS API** (Tanzania coverage)
- **Twilio** (Backup)
- **Email:** For farmers with smartphones

---

### 6. Financial Reconciliation

**Purpose:** Audit trail for accountants and regulators

**Components:**

**Daily Summary:**
- Claims filed: X
- Claims approved: Y
- Total disbursed: $Z
- Failed payments: N
- Pending balance: $P

**Monthly Report:**
- Total premium collected: $A
- Total claims paid: $B
- Loss Ratio: B/A (Target: <80%)
- Average claim amount: $C
- Fastest disbursement time: X hours
- Average disbursement time: Y hours

**Export Format:**
- **TIRA Compliance Report:** Pre-formatted Excel template
- **Audit Trail:** All claim transactions with timestamps
- **Farmer Ledger:** Individual payment history

---

## Data Model

### Claims Table Schema

```sql
CREATE TABLE claims (
    id SERIAL PRIMARY KEY,
    claim_id VARCHAR(50) UNIQUE NOT NULL, -- Format: CLM-2026-0001
    farmer_id INT REFERENCES farmers(id),
    trigger_id INT REFERENCES forecasts(id),
    trigger_type VARCHAR(50),
    trigger_date DATE,
    claim_amount DECIMAL(10,2),
    status VARCHAR(50), -- pending, approved, processing, disbursed, failed
    payment_method VARCHAR(50),
    transaction_id VARCHAR(100),
    disbursement_date TIMESTAMP,
    approved_by INT REFERENCES users(id),
    approval_date TIMESTAMP,
    failure_reason TEXT,
    retry_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_claims_status ON claims(status);
CREATE INDEX idx_claims_farmer ON claims(farmer_id);
CREATE INDEX idx_claims_trigger ON claims(trigger_id);
```

---

## API Endpoints

### Claims Management

```
GET    /api/claims                    # List all claims (with filters)
POST   /api/claims/approve-batch      # Approve trigger batch
GET    /api/claims/:id                # Get claim details
PUT    /api/claims/:id/status         # Update claim status
POST   /api/claims/:id/retry          # Retry failed payment
GET    /api/claims/stats              # Dashboard KPIs
POST   /api/claims/export             # Generate report
```

### Payment Processing

```
POST   /api/payments/process          # Initiate payment
POST   /api/payments/webhook          # Gateway callback
GET    /api/payments/:id/status       # Check payment status
```

### Notifications

```
POST   /api/notifications/send        # Send farmer notification
GET    /api/notifications/log         # Notification history
POST   /api/notifications/resend      # Resend failed notification
```

---

## User Roles & Permissions

### Claims Administrator
- Approve/reject claims batches
- Retry failed payments
- View all claims
- Export reports

### Finance Manager
- View financial summaries
- Export regulatory reports
- Cannot approve claims (separation of duties)

### System (Automated)
- Create claims from triggers
- Process payments via API
- Send notifications

---

## Compliance & Audit

### TIRA Requirements (Tanzania Insurance Regulatory Authority)

1. **Claims Register:** All claims must be logged with unique IDs
2. **Settlement Time:** Track time from trigger to disbursement
3. **Loss Ratio Reporting:** Monthly submission to TIRA
4. **Fraud Prevention:** Flag duplicate claims for same farmer/trigger
5. **Data Retention:** 7 years minimum

### Audit Trail

Every action logged:
- Who: User ID
- What: Action (approved, retried, exported)
- When: Timestamp
- Why: Notes/reason (if applicable)

---

## Future Enhancements

1. **ML-Based Fraud Detection:** Flag suspicious patterns
2. **Multi-Currency Support:** Handle USD, TZS, KES
3. **Bulk Payment via USSD:** For farmers without smartphones
4. **Integration with National ID System:** Verify farmer identity
5. **Mobile App for Farmers:** Self-service claim status checking

---

## Success Metrics

- **Disbursement Speed:** <24 hours from trigger to payment (Target)
- **Payment Success Rate:** >95% first-attempt success
- **Notification Delivery:** >90% SMS delivery rate
- **Loss Ratio:** <80% (claims/premiums)
- **Farmer Satisfaction:** >80% positive feedback

---

## Technical Stack

**Frontend:**
- React + TypeScript
- Material-UI for components
- Axios for API calls

**Backend:**
- FastAPI (Python)
- PostgreSQL database
- Redis for job queue (payment processing)

**Integrations:**
- M-Pesa API (Vodacom Tanzania)
- Africa's Talking SMS
- Leaflet for maps (farmer location visualization)

---

## Implementation Priority

**Phase 1 (MVP):**
- Claims registry table
- Manual approval workflow
- Basic payment processing (M-Pesa)
- SMS notifications

**Phase 2:**
- Automated batch approval
- Failed payment retry logic
- Email notifications
- Financial dashboards

**Phase 3:**
- Regulatory reporting automation
- Fraud detection
- Multi-payment gateway support
- Farmer mobile app

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-21  
**Owner:** Climate Insurance Tech Team
