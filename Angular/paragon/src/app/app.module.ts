import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { HomeComponent } from './components/home/home.component';
import { AboutComponent } from './components/about/about.component';
import { HowToComponent } from './components/how-to/how-to.component';
import { PageNotFoundComponent } from './components/page-not-found/page-not-found.component';

import { OktaAuthModule, OKTA_CONFIG } from '@okta/okta-angular';
import { oktaAuth } from './auth/okta-auth-config';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { InvestorsComponent } from './components/investors/investors.component';
import { provideAuth0, AuthModule} from '@auth0/auth0-angular';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { HTTP_INTERCEPTORS, provideHttpClient, withInterceptors, withInterceptorsFromDi } from '@angular/common/http';
import { AuthInterceptor } from './auth/auth-interceptor';
import { MatListModule } from '@angular/material/list';
import { ContactComponent } from './components/contact/contact.component';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { environment } from 'src/environments/environment';
import { CareersComponent } from './components/careers/careers.component';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog'

@NgModule({
  declarations: [
    AppComponent,
    HomeComponent,
    AboutComponent,
    HowToComponent,
    PageNotFoundComponent,
    InvestorsComponent,
    ContactComponent,
    CareersComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    //OktaAuthModule,
    BrowserAnimationsModule,
    MatListModule,
    MatGridListModule,
    MatCardModule,
    MatTableModule,
    MatToolbarModule,
    MatIconModule,
    MatExpansionModule,
    MatButtonModule,
    MatDialogModule,
    AuthModule.forRoot(environment.authConfig)
  ],
  providers: [/*{ provide: OKTA_CONFIG, useValue: { oktaAuth } }*/ provideAnimationsAsync(), provideHttpClient(withInterceptorsFromDi()), { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true}],
  bootstrap: [AppComponent]
})
export class AppModule { }
