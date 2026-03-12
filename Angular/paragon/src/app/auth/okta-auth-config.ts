import { OktaAuth } from '@okta/okta-auth-js';
import { provideAuth0 } from '@auth0/auth0-angular';


const oktaAuth = new OktaAuth({
    clientId: 'NbXsZlJZKqbNjgg91ECHOHEZfKGhhVdr',
    issuer: 'https://dev-5oqrhjyxiuhwflbd.us.auth0.com/oauth2/default',
    redirectUri: window.location.origin + '/login/callback',
    scopes: ['openid', 'profile', 'email', 'offline_access'],
    pkce: true,
})

export { oktaAuth }