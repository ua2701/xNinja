// components/Protected.js
import React, { useState, useEffect } from 'react';
import { useOktaAuth } from '@okta/okta-react';

const Protected = () => {
  const { authState, oktaAuth } = useOktaAuth();
  const [userInfo, setUserInfo] = useState(null);

  useEffect(() => {
    const getUserInfo = async () => {
      try {
        const info = await oktaAuth.getUser();
        setUserInfo(info);
      } catch (error) {
        console.error('Error getting user info:', error);
      }
    };
    
    if (authState?.isAuthenticated) {
      getUserInfo();
    }
  }, [authState, oktaAuth]);

  if (!authState?.isAuthenticated) {
    return (
      <div className="container mx-auto p-4 text-center">
        <p className="mb-4">
          Welcome to the <strong>Protected Page</strong>. Please get Authenticate or Login to access this private page.
        </p>
        <button
          onClick={() => oktaAuth.signInWithRedirect()}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Login with Okta
        </button>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      {userInfo && (
        <div>
          <p>
            Welcome to the <strong>Protected Page</strong>! You have successfully authenticated with Okta!
          </p>
          <div>
            <p className="mb-0">Name: {userInfo.name}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default Protected;