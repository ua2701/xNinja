// pages/Login.js
import React, { useState, useEffect } from 'react';
import { useOktaAuth } from '@okta/okta-react';

const Login = () => {
  const { oktaAuth, authState } = useOktaAuth();
  const [tokens, setTokens] = useState({
    idToken: '',
    accessToken: ''
  });

  useEffect(() => {
    const getTokens = async () => {
      if (authState?.isAuthenticated) {
        try {
          // Get the tokens from Okta
          const idToken = await oktaAuth.getIdToken();
          const accessToken = await oktaAuth.getAccessToken();
          
          setTokens({
            idToken,
            accessToken
          });
          
          // Log tokens to console for Thunder Client testing
          console.log('ID Token:', idToken);
          console.log('Access Token:', accessToken);
        } catch (error) {
          console.error('Error fetching tokens:', error);
        }
      }
    };

    getTokens();
  }, [authState, oktaAuth]);

  const login = async () => oktaAuth.signInWithRedirect();
  const logout = async () => {
    await oktaAuth.signOut();
    setTokens({ idToken: '', accessToken: '' });
  };

  if (!authState) return null;

  return (
    <div className="container mx-auto p-4">
      <p className="mb-4">
        Welcome to the <strong>Login Page</strong>. This is a public page that users use to login.
      </p>
      
      <div className="mt-4">
        {authState.isAuthenticated ? (
          <div>
            <button
              onClick={logout}
              className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded mb-4"
            >
              Logout
            </button>
            
            {/* Token Display Section */}
            <div className="mt-6 space-y-4">
              <div className="border rounded p-4">
                <h3 className="font-bold mb-2">ID Token:</h3>
                <div className="bg-gray-100 p-2 rounded break-all">
                  {tokens.idToken || 'No ID token available'}
                </div>
              </div>
              
              <div className="border rounded p-4">
                <h3 className="font-bold mb-2">Access Token:</h3>
                <div className="bg-gray-100 p-2 rounded break-all">
                  {tokens.accessToken || 'No access token available'}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <button
            onClick={login}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
          >
            Login
          </button>
        )}
      </div>
    </div>
  );
};

export default Login;