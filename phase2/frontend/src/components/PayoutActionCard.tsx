import React, { useState } from 'react';
import { Card, CardContent, Typography, Box, Button, Divider, Alert, Dialog, DialogTitle, DialogContent, DialogActions, CircularProgress, Snackbar } from '@mui/material';
import PaidIcon from '@mui/icons-material/Paid';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { claimsService } from '../services/claimsService';

interface PayoutActionCardProps {
    activeTriggers: any[];
    totalFarmers?: number;
}

const PAYOUT_RATES: Reading = {
    'drought': 60,
    'flood': 75,
    'crop_failure': 90,
    'excessive_rainfall': 75, // mapping for consistency
    'deficit_rainfall': 60    // mapping for consistency
};

type Reading = { [key: string]: number };

const PayoutActionCard: React.FC<PayoutActionCardProps> = ({
    activeTriggers = [],
    totalFarmers = 1000
}) => {
    const [dialogOpen, setDialogOpen] = useState(false);
    const [isApproving, setIsApproving] = useState(false);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    // Calculate Total Liability
    const locationLiability = new Map<number, number>();

    activeTriggers.forEach(trigger => {
        const type = trigger.alert_type?.toLowerCase() || 'drought';
        let rate = 60; // default
        if (type.includes('flood') || type.includes('excess')) rate = 75;
        else if (type.includes('fail') || type.includes('critical')) rate = 90;

        const estimatedPayout = rate * totalFarmers;

        const locId = trigger.location_id || 0;
        const currentMax = locationLiability.get(locId) || 0;
        if (estimatedPayout > currentMax) {
            locationLiability.set(locId, estimatedPayout);
        }
    });

    const totalLiability = Array.from(locationLiability.values()).reduce((a, b) => a + b, 0);
    const criticalCount = activeTriggers.filter(t => t.alert_type?.includes('critical') || t.deviation < 0).length;

    const handleApproveClick = () => {
        setDialogOpen(true);
    };

    const handleConfirmApproval = async () => {
        setIsApproving(true);
        try {
            const triggerIds = activeTriggers.map(t => t.id);
            const response = await claimsService.approveBatch({ trigger_ids: triggerIds });

            setSuccessMessage(
                `Successfully approved ${response.claims_created} claims totaling $${response.total_amount.toLocaleString()}`
            );
            setDialogOpen(false);

            // Optionally refresh dashboard data here
            setTimeout(() => window.location.reload(), 2000);
        } catch (error: any) {
            setErrorMessage(error.response?.data?.detail || 'Failed to approve claims. Please try again.');
        } finally {
            setIsApproving(false);
        }
    };

    const handleCloseDialog = () => {
        setDialogOpen(false);
    };

    return (
        <Card sx={{ border: '1px solid #ff9800', bgcolor: '#fff3e0' }}>
            <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <WarningIcon color="warning" sx={{ mr: 1, fontSize: 32 }} />
                    <Box>
                        <Typography variant="h6" fontWeight="bold">
                            Parametric Payout Liability
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                            Actionable financial impact based on active triggers
                        </Typography>
                    </Box>
                </Box>

                <Divider sx={{ my: 2 }} />

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Box>
                        <Typography variant="body2" color="text.secondary">Estimated Payout Required</Typography>
                        <Typography variant="h4" fontWeight="bold" sx={{ color: '#d32f2f' }}>
                            ${totalLiability.toLocaleString()}
                        </Typography>
                        <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }}>
                            *Based on {totalFarmers.toLocaleString()} farmers per alert location
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                            (Model A: Per-Farmer Fixed Rate)
                        </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'right' }}>
                        <Typography variant="body2" color="text.secondary">Triggers Met</Typography>
                        <Typography variant="h4" fontWeight="bold">
                            {activeTriggers.length}
                        </Typography>
                        <Typography variant="caption" color="error">
                            {criticalCount} Critical
                        </Typography>
                    </Box>
                </Box>

                <Alert severity="warning" sx={{ mb: 2 }}>
                    <strong>Action Required:</strong> {criticalCount > 0 ? 'Prepare payout disbursements for critical zones.' : 'Monitor developing patterns.'}
                </Alert>

                <Button
                    variant="contained"
                    color="warning"
                    fullWidth
                    startIcon={<PaidIcon />}
                    onClick={handleApproveClick}
                    disabled={activeTriggers.length === 0}
                >
                    Approve Payout Batch
                </Button>

                {/* Confirmation Dialog */}
                <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
                    <DialogTitle>Confirm Payout Approval</DialogTitle>
                    <DialogContent>
                        <Typography variant="body1" gutterBottom>
                            You are about to approve claims for <strong>{activeTriggers.length}</strong> active triggers.
                        </Typography>
                        <Box sx={{ my: 2, p: 2, bgcolor: '#fff3e0', borderRadius: 1 }}>
                            <Typography variant="body2" color="text.secondary">Estimated Total Payout</Typography>
                            <Typography variant="h4" fontWeight="bold" color="error">
                                ${totalLiability.toLocaleString()}
                            </Typography>
                            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                                Based on {activeTriggers.length} trigger{activeTriggers.length > 1 ? 's' : ''} × {totalFarmers.toLocaleString()} farmers per location
                            </Typography>
                        </Box>
                        <Alert severity="warning" sx={{ mt: 2 }}>
                            This will create claim records in the system. Please verify trigger data before proceeding.
                        </Alert>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={handleCloseDialog} disabled={isApproving}>
                            Cancel
                        </Button>
                        <Button
                            onClick={handleConfirmApproval}
                            variant="contained"
                            color="error"
                            disabled={isApproving}
                            startIcon={isApproving ? <CircularProgress size={20} /> : <CheckCircleIcon />}
                        >
                            {isApproving ? 'Processing...' : 'Confirm Approval'}
                        </Button>
                    </DialogActions>
                </Dialog>

                {/* Success/Error Snackbars */}
                <Snackbar
                    open={!!successMessage}
                    autoHideDuration={6000}
                    onClose={() => setSuccessMessage(null)}
                    message={successMessage}
                />
                <Snackbar
                    open={!!errorMessage}
                    autoHideDuration={6000}
                    onClose={() => setErrorMessage(null)}
                    message={errorMessage}
                />
            </CardContent>
        </Card>
    );
};

export default PayoutActionCard;
