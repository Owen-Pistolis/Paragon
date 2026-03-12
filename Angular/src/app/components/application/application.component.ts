import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators, AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms'; // Add missing imports
import { MatButtonModule } from '@angular/material/button';
import { MatError, MatFormField, MatLabel } from '@angular/material/form-field';
import { MatInput, MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { Router } from '@angular/router';
import { Job } from 'src/app/types/job';

@Component({
  selector: 'app-application',
  standalone: true,
  imports: [ReactiveFormsModule, MatError, MatLabel, MatFormField, MatInput, MatButtonModule, CommonModule, MatListModule],
  templateUrl: './application.component.html',
  styleUrls: ['./application.component.scss'],
})
export class ApplicationComponent implements OnInit {
  application: FormGroup; // Declare FormGroup type correctly
  hasUnsavedChanges: boolean = true;
  fileExtension: string = "";
  allowedExtensions: Array<string> = ["pdf"]
  invalidFile: boolean = false;
  job!: Job
  fileName: string = "";
  selectedFile!: File

  constructor(private fb: FormBuilder, private router: Router, private http: HttpClient) {
    this.application = this.fb.group({
      // Add form controls as needed
      email: ['', [ Validators.required, Validators.email ] ], // Example form control
      resume: [ null, [ Validators.required ] ],
      firstName: ['', [ Validators.required, Validators.maxLength(20) ] ],
      lastName: ['', [ Validators.required, Validators.maxLength(20) ] ],
      linkedIn: ['', [ Validators.required, linkedinValidator(), Validators.maxLength(60) ] ]
    });
  }

  ngOnInit(): void {
    this.job = window.history.state.job;
    if(this.job == null){
      this.goToCareers();
    }
    console.log(this.job)
  }

  canDeactivate(): boolean {
    if(this.job == null){
      return true;
    }
    if (this.hasUnsavedChanges) {
      return confirm(
        'Are you sure you want to leave the application page? Any progress will be lost!'
      );
    }
    return true;
  }

  onFileChange(event: any) {
    const file: File = event.target.files[0]; // Get the selected file
    if (file) {
      this.fileName = file.name;
      this.fileExtension = this.getFileExtension(this.fileName);
      if(this.allowedExtensions.includes(this.fileExtension)){
        this.invalidFile = false;
        this.selectedFile = file;
      }else{
        this.invalidFile = true;
        event.target.value = "";
        this.fileExtension = "";
      }
    }
  }

  getFileExtension(fileName: string): string {
    const ext = fileName.split('.').pop(); // Split the file name by dot and get the last part
    return ext ? ext.toLowerCase() : ''; // Return the extension, making sure it's lowercase
  }

  goToCareers(){
    this.router.navigate(["/careers"]);
  }

  submitApplication(){
    const applicationData = new FormData();
    applicationData.append("title", this.job.title)
    applicationData.append("resume", this.selectedFile);
    applicationData.append("email", this.application.controls["email"].value)
    applicationData.append("firstName", this.application.controls["firstName"].value)
    applicationData.append("lastName", this.application.controls["lastName"].value)
    applicationData.append("linkedIn", this.application.controls["linkedIn"].value)

    var response = this.http.post('https://paragonai.io:3000/api/send-email', applicationData);
    response.subscribe(
      (data) => {
        console.log('Response from the server:', data); // Handle success (data received)
      },
      (error) => {
        console.error('Error:', error); // Handle error (e.g., network error)
      }
    );
    this.application.reset()
    this.router.navigate(["/home"])
  }
}

export function linkedinValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {

    const isLinkedInValid = control.value && control.value.includes('linkedin.com');
    return !isLinkedInValid ? { 'linkedinError': 'The input must contain "linkedin.com"' } : null;
  };
}