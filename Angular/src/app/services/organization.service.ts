import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { MysqlService } from './mysql.service';

@Injectable({
  providedIn: 'root'
})
export class OrganizationService {

  constructor(private http: HttpClient, private mysql: MysqlService) { }
}
