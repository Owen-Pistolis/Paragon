import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, OnInit } from '@angular/core';
import { MysqlService } from './mysql.service';
import { User } from '../types/user';
import { environment } from 'src/environments/environment';
import { BehaviorSubject, Observable } from 'rxjs';
import { AuthService } from '@auth0/auth0-angular';

@Injectable({
  providedIn: 'root'
})
export class UserService implements OnInit {

  constructor(private http: HttpClient, private mysql: MysqlService, private auth: AuthService) { }
  private user$!: Observable<any>;
  private userInfoSubject = new BehaviorSubject<any>(null);

  userInfo$ = this.userInfoSubject.asObservable();

  ngOnInit(): void {
    this.user$ = this.auth.user$;
  }

  public addUser(user: Object){
    const headers = new HttpHeaders({
      "Content-Type": "application/json"
    });
    console.log(user);
    this.http.post(environment.APIURL + "/Users/addUser", user, {headers:headers}).subscribe({
      next: data => {
        console.log(data);
      },
      error: error => {
        console.error(error)
      }
    });
  }

  public getUser(): Observable<User> | undefined {
    const email = this.getEmail();
    if (!email) {
      console.log("Email not found!");
      return undefined;
    }
    return this.http.get<User>(environment.APIURL + "/Users/" + email);
  }

  public getEmail(){
    return this.user$ ? this.user$.subscribe(user => user?.email) : null;
  }
}