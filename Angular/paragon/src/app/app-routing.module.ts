import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { HomeComponent } from './components/home/home.component';
import { PageNotFoundComponent } from './components/page-not-found/page-not-found.component';
import { AboutComponent } from './components/about/about.component';
import { HowToComponent } from './components/how-to/how-to.component';
import { OktaAuthGuard, OktaCallbackComponent } from '@okta/okta-angular';
import { AuthGuard } from '@auth0/auth0-angular';
import { InvestorsComponent } from './components/investors/investors.component';
import { AccountComponent } from './components/account/account.component';
import { AdminPanelComponent } from './components/admin-panel/admin-panel.component';
import { ContactComponent } from './components/contact/contact.component';
import { ParagonComponent } from './components/paragon/paragon.component';
import { PrometheusComponent } from './components/prometheus/prometheus.component';
import { CareersComponent } from './components/careers/careers.component';
import { ApplicationComponent } from './components/application/application.component';
import { CanDeactivateGuard } from './guards/can-deactivate.guard';

const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'home', component: HomeComponent },
  //{ path: 'about/our-people', component: AboutComponent },
  { path: 'about/paragon', component: ParagonComponent },
  { path: 'about/prometheus', component: PrometheusComponent },
  { path: 'account', component: AccountComponent, canActivate: [ AuthGuard ] },
  { path: 'apply', component: ApplicationComponent, canDeactivate: [ CanDeactivateGuard ] },
  { path: 'careers', component: CareersComponent },
  { path: 'contact', component: ContactComponent },
  //{ path: 'howTo', component: HowToComponent },
  { path: 'investors', component: InvestorsComponent },
  //{ path: 'adminPanel', component: AdminPanelComponent },
  //{ path: 'login/callback', component: OktaCallbackComponent },
  { path: '**', component: PageNotFoundComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes, {
    scrollPositionRestoration: "enabled"
  })
],
  exports: [RouterModule]
})
export class AppRoutingModule { }
