import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { UserService } from './user.service';
import { OrganizationService } from './organization.service';
import { AuthService } from '@auth0/auth0-angular';

@Injectable({
  providedIn: 'root'
})
export class MysqlService {

  private UserAPI: UserService;
  private OrganizationAPI: OrganizationService;

  constructor(private http: HttpClient, private auth: AuthService) {
    this.UserAPI = new UserService(http, this, auth);
    this.OrganizationAPI = new OrganizationService(http, this);
   }

   getUserAPI():UserService {
    return this.UserAPI;
   }
   getOrganizationAPI():OrganizationService {
    return this.OrganizationAPI;
   }
}
