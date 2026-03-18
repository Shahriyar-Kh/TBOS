// ============================================================
// services/paymentService.ts
// ============================================================

import { api } from "@/lib/axios";
import type { ApiSuccess, PaginatedResponse } from "@/types/api";

export interface BillingDetails {
  first_name: string;
  last_name: string;
  email: string;
  country: string;
  city: string;
  postal_code: string;
  address: string;
  phone_number?: string;
}

export interface Order {
  id: string;
  order_number: string;
  course: {
    id: string;
    title: string;
    thumbnail: string;
    instructor_name: string;
  };
  amount: string;
  currency: string;
  status: "PENDING" | "COMPLETED" | "FAILED" | "REFUNDED";
  payment_method: string;
  created_at: string;
}

export interface CheckoutResponse {
  order_id: string;
  order_number: string;
  checkout_url: string;
  checkout_session_id: string;
}

const PaymentService = {
  async checkout(payload: {
    course_id: string;
    billing_details: BillingDetails;
  }): Promise<CheckoutResponse> {
    const { data } = await api.post<ApiSuccess<CheckoutResponse>>(
      "/payments/checkout/",
      payload
    );
    return data.data;
  },

  async verifyPayment(payload: {
    order_id: string;
    transaction_id: string;
  }): Promise<Order> {
    const { data } = await api.post<ApiSuccess<Order>>(
      "/payments/verify/",
      payload
    );
    return data.data;
  },

  async listMyOrders(): Promise<PaginatedResponse<Order>> {
    const { data } = await api.get<ApiSuccess<PaginatedResponse<Order>>>(
      "/payments/my-orders/"
    );
    return data.data;
  },

  async getOrder(id: string): Promise<Order> {
    const { data } = await api.get<ApiSuccess<Order>>(
      `/payments/order/${id}/`
    );
    return data.data;
  },
};

export default PaymentService;
