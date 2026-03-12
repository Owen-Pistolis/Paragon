import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router, NavigationEnd } from '@angular/router';
import { OktaAuthStateService } from '@okta/okta-angular';
import { oktaAuth } from './auth/okta-auth-config';
import { AuthService } from '@auth0/auth0-angular';
import { lastValueFrom, Observable, firstValueFrom } from 'rxjs';
import { UserService } from './services/user.service';
import { environment } from 'src/environments/environment';

declare const gtag: Function;

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {

  isAuthenticated$!: Observable<boolean>;

  constructor(private router: Router, /*public authStateService: OktaAuthStateService*/ public auth: AuthService, private route: ActivatedRoute, private userService: UserService){}
  title = 'paragon';
  loginFromPython = false;
  private themeMode = "";
  isNavVisible: boolean = false;

  ngOnInit(){
    this.isAuthenticated$ = this.auth.isAuthenticated$;
    this.isAuthenticated$.subscribe(value => console.log('Authenticated:', value));

    this.router.events.subscribe((event) => {
      if (event instanceof NavigationEnd) {
        gtag('config', environment.analyticsID, {
          page_path: event.urlAfterRedirects,
        });
      }
    });

    if(localStorage.getItem("paragonTheme") == null){
      localStorage.setItem('paragonTheme', "light");
    }
    this.themeMode = localStorage.getItem("paragonTheme") ?? "";
    this.setThemeOnRefresh();
  }
  goToHome(){
	this.router.navigate(['/home'])
  }
  login(): void {
    this.auth.loginWithRedirect()
  }
  logout(){
    this.auth.logout();
  }
  swapLogo(event: MouseEvent){

    const target = event.target as HTMLElement;
    if(this.themeMode == "light"){
      if(event.type === 'mouseenter'){
        target.setAttribute("src", "../assets/orangeLogoNoBack.png");
      } else if (event.type === 'mouseleave'){
  
        target.setAttribute("src", "../assets/blackLogoNoBack.png");
      }
    }else{
      if(event.type === 'mouseenter'){
        target.setAttribute("src", "../assets/orangeLogoNoBack.png");
      } else if (event.type === 'mouseleave'){
  
        target.setAttribute("src", "../assets/whiteLogoNoBack.png");
      }
    }

  }

  setThemeOnRefresh(){
    if(localStorage.getItem("paragonTheme") == "dark"){
      var navbar = document.getElementById("navbar-light");
      if(navbar == null) return;
      navbar.setAttribute("id", "navbar-dark");
      var logo = document.getElementById("logo");
      if(logo == null) return;
      logo.setAttribute("src", "../assets/whiteLogoNoBack.png");
      var body = document.getElementById("body-light");
      if(body == null) return;
      body.setAttribute("id", "body-dark");
    }else{
      var navbar = document.getElementById("navbar-dark");
      if(navbar == null) return;
      navbar?.setAttribute("id", "navbar-light");
      var logo = document.getElementById("logo");
      if(logo == null) return;
      logo?.setAttribute("src", "../assets/blackLogoNoBack.png")
      var body = document.getElementById("body-dark");
      if(body == null) return;
      body.setAttribute("id", "body-light");
    }
  }
  changeToLight(){
    var navbar = document.getElementById("navbar-dark");
    if(navbar == null) return;
    navbar?.setAttribute("id", "navbar-light");
    this.themeMode = "light";
    localStorage.setItem("paragonTheme", "light");
    var logo = document.getElementById("logo");
    if(logo == null) return;
    logo?.setAttribute("src", "../assets/blackLogoNoBack.png")
    var body = document.getElementById("body-dark");
    if(body == null) return;
    body.setAttribute("id", "body-light");
  }
  changeToDark(){
      var navbar = document.getElementById("navbar-light");
      if(navbar == null) return;
      navbar.setAttribute("id", "navbar-dark");
      this.themeMode = "dark";
      localStorage.setItem("paragonTheme", "dark");
      var logo = document.getElementById("logo");
      if(logo == null) return;
      logo.setAttribute("src", "../assets/whiteLogoNoBack.png");
      var body = document.getElementById("body-light");
      if(body == null) return;
      body.setAttribute("id", "body-dark");
  }
  goToContacts(){
    this.router.navigate(["/contact"]);
  }
  goToCareers(){
    this.router.navigate(["/careers"]);
  }
  toggleNav(){
    this.isNavVisible = !this.isNavVisible;
  }
}