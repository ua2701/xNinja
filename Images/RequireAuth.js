// components/RequireAuth.js
import { useOktaAuth } from '@okta/okta-react';
import { useLocation } from 'react-router-dom';
import { useEffect } from 'react';

const RequireAuth = ({ children }) => {
  const { authState } = useOktaAuth();
  const location = useLocation();

  // Simply render children or the protected content and The Protected component will handle the authentication flow
  return children;
};

export default RequireAuth;