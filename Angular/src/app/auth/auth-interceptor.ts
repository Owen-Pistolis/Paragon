import { Injectable } from '@angular/core';
import { HttpRequest, HttpHandler, HttpEvent, HttpInterceptor } from '@angular/common/http';
import { Observable, from } from 'rxjs';
import { AuthService } from '@auth0/auth0-angular';
import { switchMap } from 'rxjs/operators';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {

  constructor(private auth: AuthService) { }

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Only add an Authorization header if a token is available
    if(req.url.includes("assets/jobs.json")) return next.handle(req);
    if(req.url.includes(":3000")) return next.handle(req);
    return from(this.auth.getAccessTokenSilently()).pipe(
      switchMap(token => {
        // Clone the request and add the Authorization header if the token is available
        if (token) {
          const cloned = req.clone({
            setHeaders: {
              Authorization: `Bearer ${token}`
            }
          });
          return next.handle(cloned);
        }
        // If no token is available, pass the original request through
        return next.handle(req);
      })
    );
  }
}