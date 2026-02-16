# Santa Monica Activity Browser
This is a replacement browser for the Santa Monica city-run activities reservation website: https://anc.apm.activecommunities.com/santamonicarecreation.
The primary reason for building this site is that one must click into an activity's detail page to see what days of the week it is on.
This is especially annoying when trying to sign up for a child's swim lessons because there will be 10-12 instances of the same lesson on different days and times and each one must individually be clicked into to see when it is!
So this app provides a card browser that contains that information up front and also a calendar view.

This project is also my first time using an AI for anything. I built this with the opencode terminal and Claude Opus 4.5. So far I'm super impressed with the capability of the AI, but the code (although functional) is still quite a bit of a mess. Functionality isn't cleanly separated between modules, URL's and other settings-type stuff is hardcoded everywhere despite the existince of a settings.py file, and Claude seems to treat Python's typing system like a suggestion rather than a requirement (but hey, maybe that's the Pythonic thing to do with type hints anyhow...).

Another observation while working this small project is that Claude always jumps straight to a solution that is code based, even if the right thing to do is ask the user to run some tests first. Once I realized this and started asking things like "what test can I do to inform the next steps" the development process suddenly started going a lot faster.

Overall I got to a working MVP of the activity browser in about 4-5 20 minute sessions with Claude (using Opus 4.5 burns through my 5 hour quota pretty darn fast!).