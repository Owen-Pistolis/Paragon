import { User } from "./user"
export interface Organization {
    id: string,
    name: string,
    organizationManager: User,
    organizationManagerID: string,
    users: Array<User>

}
