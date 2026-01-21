import axios from 'axios';
import { API_BASE_URL } from '../config/api';

export interface ApproveBatchRequest {
    trigger_ids: number[];
    approved_by?: number;
}

export interface ApproveBatchResponse {
    claims_created: number;
    total_amount: number;
    claim_ids: string[];
    breakdown: {
        [key: string]: {
            count: number;
            amount: number;
        };
    };
}

export const claimsService = {
    approveBatch: async (request: ApproveBatchRequest): Promise<ApproveBatchResponse> => {
        const token = localStorage.getItem('token');
        const response = await axios.post(
            `${API_BASE_URL}/claims/approve-batch`,
            request,
            {
                headers: { Authorization: `Bearer ${token}` }
            }
        );
        return response.data;
    },

    getClaims: async (status?: string) => {
        const token = localStorage.getItem('token');
        const params = status ? { status } : {};
        const response = await axios.get(`${API_BASE_URL}/claims`, {
            headers: { Authorization: `Bearer ${token}` },
            params
        });
        return response.data;
    },

    getClaim: async (claimId: string) => {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API_BASE_URL}/claims/${claimId}`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        return response.data;
    }
};
