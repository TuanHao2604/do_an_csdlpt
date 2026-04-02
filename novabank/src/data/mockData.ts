import { User, Account, Transaction } from '../types';

export const mockUser: User = {
  id: 'u1',
  name: 'Nguyễn Văn A',
  email: 'nguyen.van.a@example.com',
};

export const mockAccounts: Account[] = [
  {
    id: 'a1',
    accountNumber: '1029 3847 5612',
    balance: 125000000,
    currency: 'VND',
    type: 'Checking',
  },
  {
    id: 'a2',
    accountNumber: '9876 5432 1098',
    balance: 500000000,
    currency: 'VND',
    type: 'Savings',
  }
];

export const mockTransactions: Transaction[] = [
  {
    id: 't1',
    date: '2026-03-25T10:30:00Z',
    description: 'Chuyển khoản cho Trần Thị B',
    amount: 5000000,
    type: 'debit',
    category: 'Transfer',
    status: 'completed',
  },
  {
    id: 't2',
    date: '2026-03-24T15:45:00Z',
    description: 'Nhận lương tháng 3',
    amount: 35000000,
    type: 'credit',
    category: 'Salary',
    status: 'completed',
  },
  {
    id: 't3',
    date: '2026-03-22T08:15:00Z',
    description: 'Thanh toán hóa đơn điện',
    amount: 1250000,
    type: 'debit',
    category: 'Utilities',
    status: 'completed',
  },
  {
    id: 't4',
    date: '2026-03-20T19:00:00Z',
    description: 'Ăn tối tại nhà hàng',
    amount: 850000,
    type: 'debit',
    category: 'Dining',
    status: 'completed',
  },
  {
    id: 't5',
    date: '2026-03-18T14:20:00Z',
    description: 'Hoàn tiền mua sắm',
    amount: 300000,
    type: 'credit',
    category: 'Shopping',
    status: 'completed',
  }
];
