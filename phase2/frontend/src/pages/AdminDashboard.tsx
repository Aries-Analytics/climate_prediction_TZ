import React, { useState, useEffect } from 'react';
import axios from '../config/axiosInstance';
import { API_BASE_URL } from '../config/api';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

interface AuditLog {
  id: number;
  user_id: number | null;
  action: string;
  resource: string;
  details: any;
  ip_address: string | null;
  created_at: string;
}

interface SystemHealth {
  status: string;
  database: string;
  users: number;
  audit_logs: number;
  forecast_logs: number;
  shadow_run_target: number;
}

const AdminDashboard: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'users' | 'audit' | 'health'>('users');
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    password: '',
    role: 'analyst'
  });

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      if (activeTab === 'users') {
        const response = await axios.get(`${API_BASE_URL}/admin/users`, { headers });
        setUsers(response.data);
      } else if (activeTab === 'audit') {
        const response = await axios.get(`${API_BASE_URL}/admin/audit-logs`, { headers });
        setAuditLogs(response.data);
      } else if (activeTab === 'health') {
        const response = await axios.get(`${API_BASE_URL}/admin/health`, { headers });
        setSystemHealth(response.data);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_BASE_URL}/admin/users`, newUser, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowCreateUser(false);
      setNewUser({ username: '', email: '', password: '', role: 'analyst' });
      fetchData();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error creating user');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_BASE_URL}/admin/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchData();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error deleting user');
    }
  };

  const handleToggleUserStatus = async (userId: number, currentStatus: boolean) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API_BASE_URL}/admin/users/${userId}`, 
        { is_active: !currentStatus },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchData();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error updating user');
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Admin Dashboard</h1>

      {/* Tabs */}
      <div className="flex space-x-4 mb-6 border-b">
        <button
          onClick={() => setActiveTab('users')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'users'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          User Management
        </button>
        <button
          onClick={() => setActiveTab('audit')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'audit'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Audit Logs
        </button>
        <button
          onClick={() => setActiveTab('health')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'health'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          System Health
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <>
          {/* User Management Tab */}
          {activeTab === 'users' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">Users ({users.length})</h2>
                <button
                  onClick={() => setShowCreateUser(true)}
                  className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                >
                  Create User
                </button>
              </div>

              {/* Create User Modal */}
              {showCreateUser && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                  <div className="bg-white rounded-lg p-6 w-full max-w-md">
                    <h3 className="text-xl font-bold mb-4">Create New User</h3>
                    <form onSubmit={handleCreateUser}>
                      <div className="mb-4">
                        <label className="block text-sm font-medium mb-1">Username</label>
                        <input
                          type="text"
                          required
                          value={newUser.username}
                          onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                          className="w-full border rounded px-3 py-2"
                        />
                      </div>
                      <div className="mb-4">
                        <label className="block text-sm font-medium mb-1">Email</label>
                        <input
                          type="email"
                          required
                          value={newUser.email}
                          onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                          className="w-full border rounded px-3 py-2"
                        />
                      </div>
                      <div className="mb-4">
                        <label className="block text-sm font-medium mb-1">Password</label>
                        <input
                          type="password"
                          required
                          value={newUser.password}
                          onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                          className="w-full border rounded px-3 py-2"
                        />
                      </div>
                      <div className="mb-4">
                        <label className="block text-sm font-medium mb-1">Role</label>
                        <select
                          value={newUser.role}
                          onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                          className="w-full border rounded px-3 py-2"
                        >
                          <option value="analyst">Analyst</option>
                          <option value="manager">Manager</option>
                          <option value="admin">Admin</option>
                        </select>
                      </div>
                      <div className="flex justify-end space-x-2">
                        <button
                          type="button"
                          onClick={() => setShowCreateUser(false)}
                          className="px-4 py-2 border rounded hover:bg-gray-100"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                        >
                          Create
                        </button>
                      </div>
                    </form>
                  </div>
                </div>
              )}

              {/* Users Table */}
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Username</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">{user.id}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">{user.username}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">{user.email}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            user.role === 'admin' ? 'bg-red-100 text-red-800' :
                            user.role === 'manager' ? 'bg-blue-100 text-blue-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {user.role}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            user.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {user.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {new Date(user.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                          <button
                            onClick={() => handleToggleUserStatus(user.id, user.is_active)}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            {user.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            className="text-red-600 hover:text-red-800"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Audit Logs Tab */}
          {activeTab === 'audit' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Audit Logs ({auditLogs.length})</h2>
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User ID</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Resource</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP Address</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {auditLogs.map((log) => (
                      <tr key={log.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {new Date(log.created_at).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">{log.user_id || 'N/A'}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">{log.action}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">{log.resource}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">{log.ip_address || 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* System Health Tab */}
          {activeTab === 'health' && systemHealth && (
            <div>
              <h2 className="text-xl font-semibold mb-4">System Health</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-sm font-medium text-gray-500 mb-2">System Status</h3>
                  <p className={`text-2xl font-bold ${
                    systemHealth.status === 'healthy' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {systemHealth.status.toUpperCase()}
                  </p>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Database</h3>
                  <p className={`text-2xl font-bold ${
                    systemHealth.database === 'connected' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {systemHealth.database.toUpperCase()}
                  </p>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Total Users</h3>
                  <p className="text-2xl font-bold text-blue-600">{systemHealth.users}</p>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Audit Logs</h3>
                  <p className="text-2xl font-bold text-purple-600">{systemHealth.audit_logs}</p>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Shadow Run Forecasts</h3>
                  <p className="text-2xl font-bold text-orange-600">
                    {systemHealth.forecast_logs} / {systemHealth.shadow_run_target}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {((systemHealth.forecast_logs / systemHealth.shadow_run_target) * 100).toFixed(1)}% complete
                  </p>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AdminDashboard;
