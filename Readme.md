### To Push new changes to repo
== 

```
docker build --tag ashjo317/ixia:ixinventorymanager.0.0.3 .  
docker run -d -p 80:3000 ashjo317/ixia:ixinventorymanager.0.0.3   (Run application locally)

docker login (To get loggged into dockerhub container registry)
docker push ashjo317/ixia:ixinventorymanager.0.0.3
```

### To run software on AWS EC2/ Any Linux Server
 
```
docker pull ashjo317/ixia:ixinventorymanager.0.0.3
docker run -d -p 80:3000 ashjo317/ixia:ixinventorymanager.0.0.3  
``` 