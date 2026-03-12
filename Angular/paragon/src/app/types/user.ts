import { Organization } from "./organization"
export interface User  {

    id: string,
    email: string,
    firstName: string,
    lastName: string,
    organization: Organization,
    organizationID: string,
    isManager: boolean,
    isAdmin: boolean,
    isOwner: boolean
}
