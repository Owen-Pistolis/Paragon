import { CanDeactivateFn } from '@angular/router';

export const CanDeactivateGuard: CanDeactivateFn<unknown> = (component: any, currentRoute, currentState, nextState) => {
    return component.canDeactivate ? component.canDeactivate() : true;
};
