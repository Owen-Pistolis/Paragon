import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatLabel, MatFormField, MatInputModule } from '@angular/material/input';
import { MatCheckbox } from '@angular/material/checkbox';
import { User } from 'src/app/types/user';
import { MysqlService } from 'src/app/services/mysql.service';

@Component({
  selector: 'app-admin-panel',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatExpansionModule,
    MatFormFieldModule,
    MatInputModule,
    MatLabel,
    MatFormField,
    MatCheckbox
  ],
  templateUrl: './admin-panel.component.html',
  styleUrls: ['./admin-panel.component.scss']
})
export class AdminPanelComponent implements OnInit {
  addUser!: FormGroup;
  addOrganization!: FormGroup;

  constructor(private fb: FormBuilder, private mysql: MysqlService) {}

  ngOnInit(): void {
    // Initialize `addUser` FormGroup
    this.addUser = this.fb.group({
      email: ['', [Validators.required, Validators.minLength(7), Validators.maxLength(30), Validators.email]],
      firstName: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(25)]],
      lastName: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(25)]],
      organization: ['', []],
      isManager: [false],
      isAdmin: [false],
      isOwner: [false],
    });

    // Initialize `addOrganization` FormGroup
    this.addOrganization = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(5), Validators.maxLength(40)]],
      organizationManagerID: ['']
    });
  }

  submitUser(): void {
    const user: User = {
      id: '',
      email: this.addUser.controls['email'].value,
      firstName: this.addUser.controls['firstName'].value,
      lastName: this.addUser.controls['lastName'].value,
      organization: this.addUser.controls['organization'].value,
      organizationID: '',
      isManager: this.addUser.controls['isManager'].value,
      isAdmin: this.addUser.controls['isAdmin'].value,
      isOwner: this.addUser.controls['isOwner'].value
    };

    const userObject = {
      ID: user.id,
      Email: user.email,
      FirstName: user.firstName,
      LastName: user.lastName,
      Organization: null,
      OrganizationID: user.organizationID,
      IsManager: user.isManager,
      IsAdmin: user.isAdmin,
      IsOwner: user.isOwner
    };

    this.mysql.getUserAPI().addUser(userObject);
  }

  submitOrganization(): void {
    // Placeholder for organization submission
    console.log('Organization submitted:', this.addOrganization.value);
  }
}



