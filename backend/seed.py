from sqlalchemy import select

from app.database import SessionLocal
from app.models import Group, GroupMember, User


def seed_database():
    with SessionLocal.begin() as session:

        # 1. Create users
        usernames = ["alice", "bob", "carol", "dan"]
        users = {}

        for username in usernames:
            user = session.scalar(
                select(User).where(User.username == username)
            )

            if user is None:
                user = User(username=username)
                session.add(user)
                session.flush()

            users[username] = user

        # 2. Create groups and their memberships
        groups_data = [
            ("Chiang Mai trip", ["alice", "bob", "carol"]),
            ("Office lunch", ["bob", "dan"]),
        ]

        for group_name, members in groups_data:
            group = session.scalar(
                select(Group).where(Group.name == group_name)
            )

            if group is None:
                group = Group(name=group_name)
                session.add(group)
                session.flush()

            # 3. Add members to each group
            for username in members:
                user = users[username]

                membership = session.get(
                    GroupMember,
                    (group.id, user.id)
                )

                if membership is None:
                    session.add(
                        GroupMember(
                            group_id=group.id,
                            user_id=user.id
                        )
                    )

    print("Seed data completed successfully!")


if __name__ == "__main__":
    seed_database()