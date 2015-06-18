# BoardManager

This is a silly, stupid HipChat bot that can keep track of whoever wants to use a resource.

## Managing resources

One user must be responsible for managing the resources. For this, they must have their
user name defined in the config.py.

### Adding a resource

To add a resource, the manager must talk to the bot:

```
<admin> @botname add resource <name>
<botname> @admin resource added
```

or

```
<botname> @admin resource already exists
```

### Removing a resource

```
<admin> @botname remove resource <name>
<botname> @admin resource removed
```

or

```
<botname> @admin I never knew <name> existed!
```

## Requesting resources

All the other users can request the usage of a resource (this includes the admin).

### "Acquiring" the resource

```
<user> @botname request <resource>
<botname> @user you're user {number} in the <resource> list.
```

or, if there is no one in the list:

```
<botname> @user there is no one using it, you're free to go.
```

or, if the user already using another resource:

```
<botname> @user stop being greedy and free <other_resource> first.
```

### Freeing the resource

When the user is done using the resource, they must notify the bot about this:

```
<user> @botname done
<botname> @user thanks
<botname> @anotheruser there is no one using <resource>, you're free to go.
```

or, if there was no one else in the resource list:

```
<botname> @all <resource> is free to use, just ask it.
```

or, if the user didn't have any resources allocated to them:

```
<botname> @user I didn't even know you were using something!
```


### Querying the resource

```
<user> @botname <resource> is free?
<botname> @user It is! Go ahead and request it!
```

or, if there is someone already using it:

```
<botname> @user No, <another user> is using it. You're not in the list, though.
```

or, if there is someone using it and the user is already in the list.

```
<botname> @user No, <another user> is using it. You're {position} after him.
```
