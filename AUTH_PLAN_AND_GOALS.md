# Authentication Plan and Goals

## Overview
This document outlines the authentication implementation plan for Bennie, focusing on a streamlined, secure, and user-friendly authentication flow that integrates with our existing onboarding process.

## User Requirements

### Authentication Flow
- Profile icon on homepage for sign-in
- Dedicated sign-in page for existing users (not modal/popup)
- No direct account creation - must go through onboarding first
- Account creation offered after successful onboarding via dedicated account creation page

### Profile Page (MVP)
- New route/page at `/profile` using dashboard-style layout
- Consistent styling with main site (same color scheme and design language)
- Display only user information initially:
  - Name
  - Email
  - Motivation to learn
  - Interests
  - Target proficiency (text description from the onboarding page's slider text box)
  - Current skill rating
- Future expansion planned for editing capabilities (not in current scope)

### Authentication Methods
Implementation order:
1. Email/Password authentication (Supabase built-in)
2. OAuth providers (implemented sequentially):
   - Google/Gmail
   - Apple
   - Facebook
   - Microsoft

Note: OAuth providers (also known as Social Authentication or SSO providers) will be implemented one at a time to ensure proper setup and testing of each integration.

### User Flow Restrictions
1. New users must start with email entry on homepage
2. Profile icon clicks by non-authenticated users redirect to sign-in page
3. Sign-in page includes note directing new users to homepage
4. Account creation only available post-onboarding
5. Account creation prompt added to onboarding success popup
6. Users can use any email for OAuth sign-in, not restricted to their Bennie communication email
   - Exception: Email/password auth must use the same email as Bennie communications

## Technical Implementation

### Database Integration (Hybrid Approach)
We will implement the hybrid approach for database integration FIRST, before building the UI components:

1. **Auth Metadata** (in auth.users)
   - Basic user information
   - Name
   - Email
   - Account preferences
   - Auth-specific data (OAuth providers, etc.)

2. **Custom Table** (our existing users table)
   - Language learning specific data
   - Progress tracking
   - Skill assessments
   - Learning preferences
   - Email interaction history

3. **Integration Method**
   - Link tables using auth.users.id as foreign key
   - Update existing user creation flow to handle both tables
   - Implement proper cascade behavior for data consistency

### Page Designs

#### Sign-in Page (`/signin`)
- Clean, centered layout matching onboarding page style
- Consistent color scheme using project variables:
  - Bittersweet (#FA7561)
  - Platinum (#E9E2DF)
  - Night (#141414)
  - Tan (#DAB785)
- Components (in order):
  1. Email/password form at top
  2. "Or sign in with..." divider
  3. OAuth provider buttons
  4. Message directing new users to homepage
- Responsive design matching existing pages

#### Profile Page (`/profile`)
- Dashboard-style layout
- Consistent styling with main site
- Sections:
  1. User Overview
     - Name
     - Email
     - Current level
  2. Language Learning Details
     - Target proficiency
     - Current skill rating
  3. Preferences
     - Motivation
     - Interests
- Each section in a distinct card/container
- Responsive grid layout

#### Updated Success Page
- Keep existing success message
- Add prominent account creation section below
- Remove homepage return option
- Clear call-to-action for account creation
- Explain benefits of having an account

## Implementation Phases

### Phase 1: Core Authentication
1. **Database Integration** (Week 1)
   - Implement hybrid approach
   - Update user creation flow
   - Migrate existing data if needed
   - Add necessary indexes and constraints

2. **Sign-in Page** (Week 1-2)
   - Create route and basic layout
   - Implement email/password authentication
   - Add form validation
   - Error handling
   - Success redirects

3. **Profile Page** (Week 2)
   - Create route and dashboard layout
   - Implement data fetching
   - Display user information
   - Add loading states
   - Error handling

4. **Update Onboarding Success** (Week 2-3)
   - Modify success popup
   - Add account creation prompt
   - Update navigation flow
   - Test complete onboarding → account creation flow

5. **Google OAuth Integration** (Week 3)
   - Set up Google OAuth credentials
   - Implement sign-in button
   - Handle OAuth flow
   - Test account creation and linking

### Phase 2: Additional OAuth Providers
Each provider will be its own 1-week sprint:
1. Apple OAuth
2. Facebook OAuth
3. Microsoft OAuth

## Security Considerations
- Secure token handling
- OAuth provider security requirements
- Password security best practices
- Rate limiting
- Session management
- CORS and CSP configuration

## Testing Requirements
- Unit tests for auth flows
- Integration tests for database operations
- E2E tests for user journeys
- OAuth provider testing
- Error handling verification
- Mobile/responsive testing

## Future Enhancements
- Additional OAuth providers
- Enhanced profile editing
- Account linking between providers
- Advanced security features (2FA, etc.)
- Profile data export/deletion capabilities

## Development Notes
- Start with database integration to avoid rework
- Maintain consistent styling across all new pages
- Follow existing project patterns for API calls
- Use existing color variables and design tokens
- Implement proper error handling from the start
- Document all OAuth provider setup steps 